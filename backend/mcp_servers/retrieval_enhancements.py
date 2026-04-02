"""
RAG Retrieval Enhancements
Provides cross-encoder re-ranking, BM25 hybrid search, MMR diversity,
and semantic relevance thresholding for improved retrieval quality.
"""

import logging
import math
import numpy as np
from typing import List, Dict

logger = logging.getLogger(__name__)

# Lazy-loaded globals to avoid import-time model loading
_cross_encoder = None
_cross_encoder_load_failed = False


def _get_cross_encoder():
    """Lazy-load cross-encoder model on first use."""
    global _cross_encoder, _cross_encoder_load_failed
    if _cross_encoder_load_failed:
        return None
    if _cross_encoder is not None:
        return _cross_encoder
    try:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        logger.info("Cross-encoder model loaded: cross-encoder/ms-marco-MiniLM-L-6-v2")
        return _cross_encoder
    except Exception as e:
        _cross_encoder_load_failed = True
        logger.warning(f"Failed to load cross-encoder model: {e}. Re-ranking disabled.")
        return None


def rerank_results(query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Re-rank search results using a cross-encoder for improved precision.

    The cross-encoder scores each (query, passage) pair jointly, producing
    much more accurate relevance scores than bi-encoder cosine similarity.

    Args:
        query: The search query
        results: List of result dicts, each must have a 'text' key
        top_k: Number of top results to return after re-ranking

    Returns:
        Re-ranked results (top_k), each with an added 'rerank_score' field
    """
    if not results:
        return results

    encoder = _get_cross_encoder()
    if encoder is None:
        return results[:top_k]

    pairs = [(query, r['text']) for r in results]

    try:
        scores = encoder.predict(pairs)

        for i, result in enumerate(results):
            result['rerank_score'] = float(scores[i])

        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        return results[:top_k]

    except Exception as e:
        logger.warning(f"Cross-encoder re-ranking failed: {e}. Returning original order.")
        return results[:top_k]


# ---------------------------------------------------------------------------
# Improvement 2: BM25 Hybrid Search with Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def bm25_score_results(query: str, candidates: List[Dict]) -> List[Dict]:
    """
    Score candidate results using BM25 for keyword relevance.

    Args:
        query: The search query
        candidates: List of result dicts with 'text' key

    Returns:
        Same candidates with 'bm25_score' added, sorted by BM25 score descending
    """
    if not candidates:
        return candidates

    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed. BM25 scoring disabled.")
        for c in candidates:
            c['bm25_score'] = 0.0
        return candidates

    # Tokenize corpus and query
    tokenized_corpus = [doc['text'].lower().split() for doc in candidates]
    tokenized_query = query.lower().split()

    try:
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        for i, candidate in enumerate(candidates):
            candidate['bm25_score'] = float(scores[i])

        return candidates

    except Exception as e:
        logger.warning(f"BM25 scoring failed: {e}")
        for c in candidates:
            c['bm25_score'] = 0.0
        return candidates


def bm25_search_postgres(query: str, model_class, top_k: int = 20,
                         filter_company: str = None) -> List[Dict]:
    """
    BM25 keyword search against PostgreSQL-stored chunks.

    Fetches chunks from the DB, scores them with BM25, returns top-k.
    At typical corpus sizes (hundreds to low thousands of chunks per company),
    this is fast enough without caching.

    Args:
        query: Search query
        model_class: Django model class (DocumentChunk or NewsChunk)
        top_k: Number of results to return
        filter_company: Optional company name filter

    Returns:
        List of result dicts with text, metadata, and bm25_score
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed. BM25 PostgreSQL search disabled.")
        return []

    try:
        # Build queryset
        qs = model_class.objects.all()

        if filter_company:
            # DocumentChunk: company is on Document, NewsChunk: has direct company FK
            if hasattr(model_class, 'document'):
                qs = qs.filter(document__company__name=filter_company)
            elif hasattr(model_class, 'company'):
                qs = qs.filter(company__name=filter_company)

        # Fetch id and text — limit to 2000 chunks to bound memory
        chunks = list(qs.values('id', 'text', 'chunk_index').order_by('-id')[:2000])

        if not chunks:
            return []

        # Build BM25 index
        tokenized_corpus = [c['text'].lower().split() for c in chunks]
        tokenized_query = query.lower().split()

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        # Attach scores and sort
        for i, chunk in enumerate(chunks):
            chunk['bm25_score'] = float(scores[i])

        chunks.sort(key=lambda x: x['bm25_score'], reverse=True)
        return chunks[:top_k]

    except Exception as e:
        logger.warning(f"BM25 PostgreSQL search failed: {e}")
        return []


def reciprocal_rank_fusion(
    vector_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60
) -> List[Dict]:
    """
    Merge vector search and BM25 results using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank)) across all retrieval sources.
    This is robust to score scale differences between retrievers.

    Args:
        vector_results: Results from vector search (ChromaDB), ordered by relevance
        bm25_results: Results from BM25 search, ordered by BM25 score
        k: RRF constant (default 60, standard value from the RRF paper)

    Returns:
        Merged and de-duplicated results sorted by RRF score
    """
    # Score map: unique_key -> {result_dict, rrf_score}
    fused = {}

    def _result_key(result: Dict) -> str:
        """Generate unique key for de-duplication."""
        meta = result.get('metadata', {})
        doc_id = meta.get('document_id', result.get('id', ''))
        chunk_idx = meta.get('chunk_index', result.get('chunk_index', ''))
        return f"{doc_id}_{chunk_idx}"

    # Score vector results by rank
    for rank, result in enumerate(vector_results):
        key = _result_key(result)
        rrf_score = 1.0 / (k + rank + 1)
        if key in fused:
            fused[key]['rrf_score'] += rrf_score
        else:
            fused[key] = {**result, 'rrf_score': rrf_score}

    # Score BM25 results by rank
    for rank, result in enumerate(bm25_results):
        key = _result_key(result)
        rrf_score = 1.0 / (k + rank + 1)
        if key in fused:
            fused[key]['rrf_score'] += rrf_score
        else:
            # BM25-only result — need to build a full result dict
            fused[key] = {
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'distance': None,
                'bm25_score': result.get('bm25_score', 0.0),
                'rrf_score': rrf_score,
            }

    # Sort by RRF score descending
    merged = sorted(fused.values(), key=lambda x: x['rrf_score'], reverse=True)
    return merged


# ---------------------------------------------------------------------------
# Improvement 3: Maximum Marginal Relevance (MMR) Diversity
# ---------------------------------------------------------------------------

def mmr_diversify(results: List[Dict], top_k: int = 5, lambda_param: float = 0.7) -> List[Dict]:
    """
    Apply Maximum Marginal Relevance to diversify search results.

    Iteratively selects results that balance relevance (high score) with
    novelty (low similarity to already-selected results). Prevents returning
    5 near-identical chunks from the same document section.

    Uses TF-IDF vectors for lightweight pairwise similarity — no model needed.

    Args:
        results: Pre-scored results (must have 'rerank_score' or 'rrf_score' or 'distance')
        top_k: Number of results to select
        lambda_param: Balance between relevance (1.0) and diversity (0.0).
                      0.7 = favor relevance, still penalize redundancy.

    Returns:
        Diversified subset of results
    """
    if len(results) <= top_k:
        return results

    # Extract texts for similarity computation
    texts = [r['text'] for r in results]

    # Build TF-IDF similarity matrix using simple word-count vectors
    tfidf_matrix = _compute_tfidf_matrix(texts)

    # Get relevance scores (prefer rerank_score > rrf_score > inverse distance)
    relevance_scores = []
    for r in results:
        if 'rerank_score' in r:
            relevance_scores.append(r['rerank_score'])
        elif 'rrf_score' in r:
            relevance_scores.append(r['rrf_score'])
        elif r.get('distance') is not None:
            relevance_scores.append(1.0 - r['distance'])
        else:
            relevance_scores.append(0.5)
    relevance_scores = np.array(relevance_scores)

    # Normalize relevance to [0, 1]
    r_min, r_max = relevance_scores.min(), relevance_scores.max()
    if r_max > r_min:
        relevance_scores = (relevance_scores - r_min) / (r_max - r_min)

    # Greedy MMR selection
    selected_indices = []
    remaining = set(range(len(results)))

    for _ in range(top_k):
        if not remaining:
            break

        best_idx = None
        best_mmr = -float('inf')

        for idx in remaining:
            relevance = relevance_scores[idx]

            # Max similarity to any already-selected result
            if selected_indices:
                similarities = [
                    _cosine_sim_tfidf(tfidf_matrix[idx], tfidf_matrix[s])
                    for s in selected_indices
                ]
                max_sim = max(similarities)
            else:
                max_sim = 0.0

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining.discard(best_idx)

    return [results[i] for i in selected_indices]


def _compute_tfidf_matrix(texts: List[str]) -> List[Dict[str, float]]:
    """
    Compute simple TF-IDF vectors for a list of texts.
    Returns a list of {term: tfidf_weight} dicts.
    """

    # Tokenize
    tokenized = [text.lower().split() for text in texts]
    n_docs = len(tokenized)

    # Document frequency
    df = {}
    for tokens in tokenized:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    # IDF
    idf = {term: math.log(n_docs / count) for term, count in df.items()}

    # TF-IDF per document
    tfidf_vectors = []
    for tokens in tokenized:
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = len(tokens) if tokens else 1
        vec = {t: (count / total) * idf.get(t, 0) for t, count in tf.items()}
        tfidf_vectors.append(vec)

    return tfidf_vectors


def _cosine_sim_tfidf(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors."""
    # Dot product over shared terms
    shared_terms = set(vec_a.keys()) & set(vec_b.keys())
    if not shared_terms:
        return 0.0

    dot = sum(vec_a[t] * vec_b[t] for t in shared_terms)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Improvement 4: Semantic Relevance Threshold
# ---------------------------------------------------------------------------

def apply_relevance_threshold(
    results: List[Dict],
    min_score: float = -2.0,
    score_key: str = 'rerank_score'
) -> List[Dict]:
    """
    Filter out results below a minimum relevance score.

    Applied as the final pipeline step to prevent feeding the LLM with
    irrelevant chunks that happen to be "least dissimilar."

    The cross-encoder (ms-marco-MiniLM-L-6-v2) outputs logits roughly in
    [-10, +10]. Empirically:
      > 0: likely relevant
      -2 to 0: borderline
      < -2: likely irrelevant

    Args:
        results: Results with score_key field (from cross-encoder re-ranking)
        min_score: Minimum score to keep. Default -2.0 (conservative).
        score_key: Which score field to threshold on.

    Returns:
        Filtered results. Returns at least 1 result if any exist (never empty
        when input is non-empty), to avoid "no results found" for edge cases.
    """
    if not results:
        return results

    filtered = [r for r in results if r.get(score_key, 0) >= min_score]

    # Always return at least the top result to avoid empty responses
    if not filtered and results:
        return results[:1]

    return filtered
