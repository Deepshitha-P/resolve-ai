import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# ΓöÇΓöÇ Change 1: Product/Region query extractor ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Same keyword sets as stage04_nlp._PRODUCT_KEYWORDS / _REGION_KEYWORDS.
_QUERY_PRODUCTS = {
    "broadband": ["broadband", "fibre", "fiber", "dsl"],
    "wifi":      ["wifi", "wi-fi", "wireless"],
    "internet":  ["internet", "net connection"],
    "sim":       ["sim card", "sim", "esim"],
    "app":       ["app", "application", "mobile app"],
    "phone":     ["phone", "handset", "mobile", "smartphone"],
    "flight":    ["flight", "airline", "air ticket"],
    "ticket":    ["ticket", "booking", "reservation"],
    "router":    ["router", "modem", "hub"],
    "line":      ["line", "landline", "telephone line"],
    "tv":        ["tv", "television", "cable", "satellite"],
    "streaming": ["streaming", "video", "netflix", "disney"],
}
_QUERY_REGIONS = {
    "london":     ["london", "uk", "england", "britain"],
    "manchester": ["manchester"],
    "birmingham": ["birmingham"],
    "glasgow":    ["glasgow", "scotland"],
    "chennai":    ["chennai", "madras", "anna nagar"],
    "mumbai":     ["mumbai", "bombay"],
    "delhi":      ["delhi", "new delhi"],
    "bangalore":  ["bangalore", "bengaluru"],
    "hyderabad":  ["hyderabad"],
    "new_york":   ["new york", "nyc"],
    "california": ["california", "los angeles", "san francisco"],
    "texas":      ["texas", "houston", "dallas"],
    # Generic region tokens (e.g. "Region X" in test queries)
    "region_x":   ["region x"],
    "region_a":   ["region a"],
    "region_b":   ["region b"],
}


def extract_product_region_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Change 1: Detect explicit product/region mentions in a query string.
    Returns (product, region) ΓÇö either may be None if not mentioned.
    Used to apply metadata boosts in hybrid_search().
    """
    clean = query.lower()
    product: Optional[str] = None
    region:  Optional[str] = None
    for prod_name, kws in _QUERY_PRODUCTS.items():
        if any(kw in clean for kw in kws):
            product = prod_name
            break
    for reg_name, kws in _QUERY_REGIONS.items():
        if any(kw in clean for kw in kws):
            region = reg_name
            break
    return product, region


class BM25:
    """Minimal, dependency-free BM25 (Okapi) implementation."""

    def __init__(self, texts: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tokenized = [self._tokenize(t) for t in texts]
        self.doc_lens = [len(t) for t in self.tokenized]
        self.avgdl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        self.df = Counter()
        for toks in self.tokenized:
            for term in set(toks):
                self.df[term] += 1
        self.N = len(texts)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", str(text).lower())

    def _idf(self, term: str) -> float:
        n_q = self.df.get(term, 0)
        return math.log(1 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def score(self, query: str) -> List[float]:
        if self.N == 0:
            return []
        q_terms = self._tokenize(query)
        scores = [0.0] * self.N
        for i, toks in enumerate(self.tokenized):
            tf = Counter(toks)
            dl = self.doc_lens[i]
            s = 0.0
            for term in q_terms:
                if term not in tf:
                    continue
                idf = self._idf(term)
                freq = tf[term]
                s += idf * (freq * (self.k1 + 1)) / (freq + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9)))
            scores[i] = s
        return scores


def hybrid_search(
    query: str,
    docs: List[Dict],
    embedder,
    doc_vectors,
    bm25: BM25,
    top_k: int = 5,
    alpha: float = 0.5,
    query_vec=None,  # pre-encoded query vector; if provided, skip re-encoding
) -> List[Dict]:
    """alpha weights vector score vs keyword score: combined = alpha*vec + (1-alpha)*bm25"""
    if not docs:
        return []

    if query_vec is None:
        query_vec = embedder.encode([query])
    # Ensure dense 2-D arrays (handle scipy sparse from TF-IDF)
    import numpy as np
    if hasattr(query_vec, 'toarray'):
        query_vec = query_vec.toarray()
    query_vec = np.atleast_2d(query_vec)
    _doc_vecs = doc_vectors
    if hasattr(_doc_vecs, 'toarray'):
        _doc_vecs = _doc_vecs.toarray()
    _doc_vecs = np.atleast_2d(_doc_vecs)
    vec_scores = cosine_similarity(query_vec, _doc_vecs).flatten()
    bm25_scores = bm25.score(query)

    def _norm(arr):
        arr = list(arr)
        lo, hi = min(arr), max(arr)
        if hi - lo < 1e-9:
            return [1.0 if x > 0 else 0.0 for x in arr]
        return [(x - lo) / (hi - lo) for x in arr]


    vec_n  = _norm(vec_scores)
    bm25_n = _norm(bm25_scores)

    combined = [alpha * v + (1 - alpha) * b for v, b in zip(vec_n, bm25_n)]

    # Change 1: soft boost (+20%) for results whose metadata.product or
    # metadata.region matches an explicit mention in the query.
    q_product, q_region = extract_product_region_from_query(query)
    BOOST = 1.2
    for i, doc in enumerate(docs):
        meta = doc.get("metadata") or {}
        d_product = meta.get("product") or doc.get("product", "unknown")
        d_region  = meta.get("region")  or doc.get("region",  "unknown")
        if (q_product and d_product == q_product) or (q_region and d_region == q_region):
            combined[i] = min(combined[i] * BOOST, 1.0)

    ranked_idx = sorted(range(len(docs)), key=lambda i: combined[i], reverse=True)[:top_k]

    results = []
    for i in ranked_idx:
        if combined[i] > 0:
            doc = docs[i]
            meta = doc.get("metadata") or {}
            results.append({
                "doc":            doc,
                "layer":          doc.get("type") or doc.get("document_type", "unknown"),
                "doc_id":         doc.get("doc_id") or doc.get("document_id"),
                "title":          doc.get("title", ""),
                "text":           doc.get("text") or doc.get("content", ""),
                "metadata":       meta,
                "product":        meta.get("product") or doc.get("product", "unknown"),  # Change 1
                "region":         meta.get("region")  or doc.get("region",  "unknown"),  # Change 1
                "vector_score":   round(vec_n[i], 4),
                "keyword_score":  round(bm25_n[i], 4),
                "combined_score": round(combined[i], 4),
            })
    return results


def hybrid_search_layers(
    query: str,
    target_docs: List[Dict],
    embedder,
    top_k: int = 5,
    alpha: float = 0.5,
    max_dense_docs: int = 200,
) -> List[Dict]:
    """
    Performs hybrid retrieval over router-selected target layers.

    Speed optimisation (Fix #3):
      Pre-screen with BM25 (cheap, O(n)) to select the top `max_dense_docs`
      candidates, then only dense-encode that short-list.  This reduces the
      embedder call from O(all_routed_docs) to O(min(n, max_dense_docs)).
    """
    if not target_docs:
        return []

    texts = [(d.get("title") or "") + ". " + (d.get("text") or d.get("content") or "") for d in target_docs]
    bm25 = BM25(texts)

    # ΓöÇΓöÇ Pre-screen with BM25 so dense encoding stays O(max_dense_docs) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    if len(target_docs) > max_dense_docs:
        bm25_raw = bm25.score(query)
        # Pick top-max_dense_docs by BM25; keep at least top_k
        keep_n = max(max_dense_docs, top_k)
        top_idx = sorted(range(len(target_docs)), key=lambda i: bm25_raw[i], reverse=True)[:keep_n]
        target_docs = [target_docs[i] for i in top_idx]
        texts        = [texts[i]       for i in top_idx]
        # Rebuild BM25 on the short-list (scores stay consistent)
        bm25 = BM25(texts)

    # Encode query + short-listed docs in ONE call so TF-IDF vocab is consistent
    all_texts = [query] + texts
    all_vectors = embedder.encode(all_texts)
    import numpy as np
    if hasattr(all_vectors, 'toarray'):
        all_vectors = all_vectors.toarray()
    all_vectors = np.atleast_2d(all_vectors)
    query_vec  = all_vectors[:1]    # shape (1, dim)
    doc_vectors = all_vectors[1:]   # shape (n, dim)

    return hybrid_search(
        query, target_docs, embedder, doc_vectors, bm25,
        top_k=top_k, alpha=alpha, query_vec=query_vec
    )


# ── Pre-computed layer index for fast repeated queries ──────────────────

def build_layer_index(
    chunked_docs: List[Dict],
    embedder,
) -> Dict[str, Dict]:
    """
    Pre-compute per-layer BM25 indexes and dense doc vectors at batch-pipeline
    time.  Returned dict maps layer_name -> { docs, texts, bm25, doc_vectors }.

    At query time, `hybrid_search_precomputed` uses these artifacts directly,
    avoiding the two most expensive per-query operations:
      1. BM25 construction  (~50-200 ms per call)
      2. Batch doc embedding (~1-4 s per call for hundreds of docs)

    IMPORTANT: When fastembed falls back to TF-IDF, independent per-layer fits
    produce different vocabulary sizes (e.g. 2000 vs 502), making np.vstack
    fail at query time.  We therefore encode ALL texts in one shot so the
    embedder (whether dense or TF-IDF) produces vectors with a consistent dim,
    then slice back into per-layer arrays.
    """
    from collections import defaultdict

    # Group docs by layer type
    layer_groups: Dict[str, List[Dict]] = defaultdict(list)
    for d in chunked_docs:
        layer = d.get("type") or d.get("document_type") or "unknown"
        layer_groups[layer].append(d)

    # Build per-layer text lists and record their slice boundaries
    layer_names: List[str] = list(layer_groups.keys())
    layer_texts: List[List[str]] = []
    for ln in layer_names:
        texts = [
            (d.get("title") or "") + ". " + (d.get("text") or d.get("content") or "")
            for d in layer_groups[ln]
        ]
        layer_texts.append(texts)

    # Encode ALL texts in one call -> guaranteed consistent embedding dimension
    all_texts_flat = [t for lt in layer_texts for t in lt]
    all_vectors = embedder.encode(all_texts_flat) if all_texts_flat else np.zeros((0, 1))
    if hasattr(all_vectors, 'toarray'):
        all_vectors = all_vectors.toarray()
    all_vectors = np.atleast_2d(all_vectors)

    # Slice back into per-layer chunks and build BM25 per layer
    layer_index: Dict[str, Dict] = {}
    offset = 0
    for ln, texts in zip(layer_names, layer_texts):
        n = len(texts)
        doc_vectors = all_vectors[offset: offset + n]
        offset += n
        bm25 = BM25(texts)
        layer_index[ln] = {
            "docs": layer_groups[ln],
            "texts": texts,
            "bm25": bm25,
            "doc_vectors": doc_vectors,
        }

    return layer_index


def hybrid_search_precomputed(
    query: str,
    selected_layers: List[str],
    layer_index: Dict[str, Dict],
    embedder,
    top_k: int = 5,
    alpha: float = 0.5,
    query_vec=None,
) -> List[Dict]:
    """
    Fast hybrid retrieval using pre-computed per-layer BM25 + doc vectors.

    Instead of rebuilding everything per query, this:
      1. Looks up pre-built artifacts from layer_index
      2. Merges docs from all selected layers
      3. Encodes only the query (single string, ~10 ms)
      4. Runs cosine similarity + BM25 scoring on pre-built structures

    Falls back to hybrid_search_layers if a requested layer is missing
    from the index.
    """
    # Collect docs + vectors from pre-computed layers
    all_docs = []
    all_vectors_list = []
    all_texts = []
    missing_layers = []

    for layer in selected_layers:
        entry = layer_index.get(layer)
        if entry:
            all_docs.extend(entry["docs"])
            all_vectors_list.append(entry["doc_vectors"])
            all_texts.extend(entry["texts"])
        else:
            missing_layers.append(layer)

    # If nothing matched in precomputed index, fall back to all docs across all layers
    if not all_docs:
        for entry in layer_index.values():
            all_docs.extend(entry["docs"])
            all_vectors_list.append(entry["doc_vectors"])
            all_texts.extend(entry["texts"])

    if not all_docs:
        return []

    # Stack doc vectors
    doc_vectors = np.vstack(all_vectors_list)

    # Build merged BM25 for the combined text set
    bm25 = BM25(all_texts)

    # Encode only the query (single embedding call ~10ms)
    if query_vec is None:
        query_vec = embedder.encode([query])
    if hasattr(query_vec, 'toarray'):
        query_vec = query_vec.toarray()
    query_vec = np.atleast_2d(query_vec)

    return hybrid_search(
        query, all_docs, embedder, doc_vectors, bm25,
        top_k=top_k, alpha=alpha, query_vec=query_vec,
    )
