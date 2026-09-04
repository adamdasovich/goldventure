"""
Gunicorn configuration. Discovered automatically because the systemd unit's
WorkingDirectory is this directory (gunicorn reads ./gunicorn.conf.py by
default); command-line flags in ExecStart take precedence over anything here,
so this file only adds hooks.

NOTE: a newly added config file is only picked up by a full
`systemctl restart gunicorn` — HUP re-reads the file it found at startup.
"""

import logging
import threading

logger = logging.getLogger("gunicorn.error")


def post_worker_init(worker):
    """
    Warm the RAG stack in the background as each worker boots.

    Building the shared RAGManager pulls in voyageai -> transformers -> torch,
    loads the cross-encoder, and connects to ChromaDB — ~20-25s that the first
    chat request touching a RAG tool otherwise pays. Workers recycle every
    ~1000 requests (--max-requests), so without this the stall comes back
    periodically, not just after deploys.

    Runs in a daemon thread so the worker starts serving immediately; a chat
    request arriving mid-warmup simply waits on get_rag_manager()'s lock
    instead of duplicating the work.
    """

    def warm():
        # The two warmups are independent — a stopped chromadb.service must
        # not also skip the cross-encoder load (and vice versa). Warmup is
        # best-effort either way: a failure must not kill the worker, and the
        # lazy path still works.
        try:
            from mcp_servers.rag_utils import get_rag_manager
            get_rag_manager()
        except Exception:
            logger.exception("RAGManager warmup failed (worker pid %s)", worker.pid)

        try:
            from mcp_servers.retrieval_enhancements import rerank_results
            # First cross-encoder predict pays one-time allocation cost too.
            rerank_results("warmup", [{"text": "warmup"}], top_k=1)
        except Exception:
            logger.exception("Cross-encoder warmup failed (worker pid %s)", worker.pid)

        logger.info("RAG warmup complete (worker pid %s)", worker.pid)

    threading.Thread(target=warm, name="rag-warmup", daemon=True).start()
