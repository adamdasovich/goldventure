"""
ChromaDB Subprocess Isolation Module

Runs ChromaDB operations in a separate subprocess to protect against SIGSEGV crashes.
The Rust bindings in ChromaDB can cause segmentation faults that bypass Python exception
handling and kill the entire process. By running in a subprocess, we isolate these crashes
so the main Celery worker survives.

See: https://github.com/chroma-core/chroma/issues/4365
"""

import logging
import multiprocessing
import json
import sys
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _subprocess_process_news(company_name: str, company_id: int, limit: int, result_queue: multiprocessing.Queue):
    """
    Worker function that runs in a subprocess.
    Processes news content into ChromaDB.

    IMPORTANT: This function runs in a SEPARATE PROCESS.
    If it crashes (SIGSEGV), only this subprocess dies.
    """
    try:
        # Setup Django in subprocess
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()

        from mcp_servers.news_content_processor import NewsContentProcessor

        processor = NewsContentProcessor(company_id=company_id)
        result = processor._process_company_news(company_name, limit=limit)

        result_queue.put({
            'success': True,
            'result': result
        })
    except Exception as e:
        result_queue.put({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        })


def process_company_news_isolated(company_name: str, company_id: int, limit: int = 25, timeout: int = 120) -> Dict:
    """
    Process company news in an isolated subprocess.

    This wraps NewsContentProcessor._process_company_news() in a subprocess
    to protect against SIGSEGV crashes from ChromaDB's Rust bindings.

    Args:
        company_name: Name of the company to process
        company_id: ID of the company in the database
        limit: Maximum number of news items to process
        timeout: Maximum seconds to wait for the subprocess

    Returns:
        dict with keys:
        - success: bool
        - result: dict (if success) containing news_items_processed, chunks_created
        - error: str (if failed)
        - crash: bool (if subprocess crashed with SIGSEGV)
    """
    # Use spawn context to get a clean process (no shared state)
    ctx = multiprocessing.get_context('spawn')
    result_queue = ctx.Queue()

    process = ctx.Process(
        target=_subprocess_process_news,
        args=(company_name, company_id, limit, result_queue),
        name=f"chromadb-processor-{company_id}"
    )

    try:
        process.start()
        process.join(timeout=timeout)

        if process.is_alive():
            # Timeout - kill the subprocess
            logger.warning(f"ChromaDB processing timeout for {company_name} (>{timeout}s), killing subprocess")
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
            return {
                'success': False,
                'error': f'Processing timeout after {timeout}s',
                'timeout': True
            }

        # Check exit code
        if process.exitcode != 0:
            # Non-zero exit code indicates crash (SIGSEGV = -11 on Linux)
            exit_code = process.exitcode
            if exit_code == -11:
                logger.error(f"ChromaDB subprocess SIGSEGV crash for {company_name} (signal 11)")
                return {
                    'success': False,
                    'error': 'ChromaDB subprocess crashed with SIGSEGV (signal 11)',
                    'crash': True,
                    'exit_code': exit_code
                }
            else:
                logger.error(f"ChromaDB subprocess crashed for {company_name} (exit code: {exit_code})")
                return {
                    'success': False,
                    'error': f'Subprocess crashed with exit code {exit_code}',
                    'crash': True,
                    'exit_code': exit_code
                }

        # Get result from queue
        try:
            result = result_queue.get(timeout=1)
            return result
        except Exception:
            return {
                'success': False,
                'error': 'Failed to get result from subprocess'
            }

    except Exception as e:
        logger.error(f"Error running ChromaDB subprocess for {company_name}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Cleanup
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)


def process_news_batch_isolated(companies: list, limit_per_company: int = 20, timeout_per_company: int = 120) -> Dict:
    """
    Process news for multiple companies, each in an isolated subprocess.

    Args:
        companies: List of dicts with 'name' and 'id' keys
        limit_per_company: Max news items per company
        timeout_per_company: Timeout in seconds per company

    Returns:
        dict with processing stats
    """
    results = {
        'total_companies': len(companies),
        'processed': 0,
        'crashed': 0,
        'timeout': 0,
        'failed': 0,
        'total_chunks': 0,
        'total_news_items': 0,
        'errors': []
    }

    for company in companies:
        company_name = company.get('name', 'Unknown')
        company_id = company.get('id')

        if not company_id:
            results['failed'] += 1
            results['errors'].append(f"{company_name}: Missing company ID")
            continue

        result = process_company_news_isolated(
            company_name=company_name,
            company_id=company_id,
            limit=limit_per_company,
            timeout=timeout_per_company
        )

        if result.get('success'):
            results['processed'] += 1
            inner_result = result.get('result', {})
            results['total_chunks'] += inner_result.get('chunks_created', 0)
            results['total_news_items'] += inner_result.get('news_items_processed', 0)
            logger.info(f"  ChromaDB: Processed {inner_result.get('news_items_processed', 0)} items, "
                       f"{inner_result.get('chunks_created', 0)} chunks for {company_name}")
        elif result.get('crash'):
            results['crashed'] += 1
            results['errors'].append(f"{company_name}: {result.get('error', 'Subprocess crash')}")
            logger.warning(f"  ChromaDB: Subprocess crashed for {company_name} (isolated, worker survived)")
        elif result.get('timeout'):
            results['timeout'] += 1
            results['errors'].append(f"{company_name}: {result.get('error', 'Timeout')}")
            logger.warning(f"  ChromaDB: Processing timeout for {company_name}")
        else:
            results['failed'] += 1
            results['errors'].append(f"{company_name}: {result.get('error', 'Unknown error')}")

    return results


def _subprocess_store_profile(company_id: int, result_queue: multiprocessing.Queue):
    """
    Worker function that runs in a subprocess.
    Stores company profile in ChromaDB.

    IMPORTANT: This function runs in a SEPARATE PROCESS.
    If it crashes (SIGSEGV), only this subprocess dies.
    """
    try:
        # Setup Django in subprocess
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()

        import chromadb
        from chromadb.config import Settings as ChromaSettings
        from pathlib import Path
        from django.conf import settings
        from mcp_servers.embeddings import get_embedding_function
        from core.models import Company

        company = Company.objects.get(id=company_id)

        # Build company profile text
        profile_parts = []

        if company.description:
            profile_parts.append(f"Company Overview: {company.name}\n{company.description}")

        if company.tagline:
            profile_parts.append(f"Tagline: {company.tagline}")

        if company.ticker_symbol and company.exchange:
            profile_parts.append(f"Stock: {company.ticker_symbol} on {company.exchange.upper()}")

        # Projects summary
        projects = company.projects.all()
        if projects:
            project_texts = []
            for project in projects:
                project_text = f"Project: {project.name}"
                if project.description:
                    project_text += f"\n{project.description}"
                if project.country:
                    project_text += f"\nLocation: {project.country}"
                if project.primary_commodity:
                    project_text += f"\nCommodity: {project.primary_commodity}"
                project_texts.append(project_text)
            profile_parts.append("Projects:\n" + "\n\n".join(project_texts))

        if not profile_parts:
            result_queue.put({
                'success': True,
                'result': {'status': 'skipped', 'message': 'No profile data to store'}
            })
            return

        full_profile = "\n\n".join(profile_parts)

        # Store in ChromaDB
        chroma_path = Path(settings.BASE_DIR) / "chroma_db"
        chroma_path.mkdir(exist_ok=True)

        chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get embedding function
        embedding_function = get_embedding_function()

        collection = chroma_client.get_or_create_collection(
            name="company_profiles",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_function
        )

        # Delete existing profile
        try:
            collection.delete(ids=[f"company_{company.id}_profile"])
        except Exception:
            pass  # Profile may not exist yet

        # Add profile
        collection.add(
            ids=[f"company_{company.id}_profile"],
            documents=[full_profile],
            metadatas=[{
                "company_id": company.id,
                "company_name": company.name,
                "ticker": company.ticker_symbol or "",
                "exchange": company.exchange or "",
                "type": "company_profile"
            }]
        )

        result_queue.put({
            'success': True,
            'result': {
                'status': 'success',
                'company': company.name,
                'chars_stored': len(full_profile)
            }
        })
    except Exception as e:
        result_queue.put({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        })


def store_company_profile_isolated(company_id: int, timeout: int = 60) -> Dict:
    """
    Store company profile in ChromaDB using an isolated subprocess.

    Args:
        company_id: ID of the company to store profile for
        timeout: Maximum seconds to wait for the subprocess

    Returns:
        dict with keys:
        - success: bool
        - result: dict (if success)
        - error: str (if failed)
        - crash: bool (if subprocess crashed with SIGSEGV)
    """
    # Use spawn context to get a clean process (no shared state)
    ctx = multiprocessing.get_context('spawn')
    result_queue = ctx.Queue()

    process = ctx.Process(
        target=_subprocess_store_profile,
        args=(company_id, result_queue),
        name=f"chromadb-profile-{company_id}"
    )

    try:
        process.start()
        process.join(timeout=timeout)

        if process.is_alive():
            # Timeout - kill the subprocess
            logger.warning(f"ChromaDB profile storage timeout for company {company_id} (>{timeout}s)")
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
            return {
                'success': False,
                'error': f'Processing timeout after {timeout}s',
                'timeout': True
            }

        # Check exit code
        if process.exitcode != 0:
            exit_code = process.exitcode
            if exit_code == -11:
                logger.error(f"ChromaDB profile subprocess SIGSEGV crash for company {company_id}")
                return {
                    'success': False,
                    'error': 'ChromaDB subprocess crashed with SIGSEGV (signal 11)',
                    'crash': True,
                    'exit_code': exit_code
                }
            else:
                logger.error(f"ChromaDB profile subprocess crashed for company {company_id} (exit: {exit_code})")
                return {
                    'success': False,
                    'error': f'Subprocess crashed with exit code {exit_code}',
                    'crash': True,
                    'exit_code': exit_code
                }

        # Get result from queue
        try:
            result = result_queue.get(timeout=1)
            return result
        except Exception:
            return {
                'success': False,
                'error': 'Failed to get result from subprocess'
            }

    except Exception as e:
        logger.error(f"Error running ChromaDB profile subprocess for company {company_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Cleanup
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
