"""
stage11_vector_db.py

ChromaDB-backed persistent vector store for the RootIQ RAG pipeline.

Classes:
  ChromaVectorDB   ΓÇö Single Chroma collection. Replaces the old in-memory VectorDB.
  LayeredVectorDB  ΓÇö Layer-partitioned store (separate Chroma collection per layer).
  VectorDB         ΓÇö Legacy in-memory fallback (used if chromadb is not installed).

ChromaDB uses its built-in sentence-transformers embedding function by default,
so you do NOT need to pass pre-computed vectors ΓÇö just pass the raw texts.

Config (read from .env):
  CHROMA_PERSIST_DIR   = ./data/chroma_db
  CHROMA_COLLECTION    = rootiq_knowledge
"""

import os
from typing import Any, Dict, List, Optional

import numpy as np

# ΓöÇΓöÇ Load .env ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma_db")
CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "rootiq_knowledge")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# ChromaDB Vector Store
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class ChromaVectorDB:
    """
    Persistent vector store backed by ChromaDB.

    Chroma generates embeddings internally using its default
    all-MiniLM-L6-v2 sentence-transformers model ΓÇö no external embedding
    call required.  Documents are stored with full metadata so that
    search() returns rich result dicts compatible with the rest of the
    RootIQ pipeline.

    Usage:
        vdb = ChromaVectorDB(collection_name="rootiq_knowledge")
        vdb.add(docs)                        # indexes chunked docs
        results = vdb.search("query", top_k=5)
    """

    def __init__(
        self,
        collection_name: str = CHROMA_COLLECTION,
        persist_dir: str = CHROMA_PERSIST_DIR,
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None
        self._available = self._try_init()
        # ΓöÇΓöÇ count() cache to avoid a Chroma round-trip on every search() ΓöÇΓöÇΓöÇ
        self._cached_count: int = -1
        self._cached_count_ts: float = 0.0
        self._COUNT_TTL: float = 60.0  # seconds

    # ΓöÇΓöÇ Initialisation ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def _try_init(self) -> bool:
        """Attempt to connect to / create a Chroma collection. Returns True on success."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)

            # Use FastEmbed by default if installed, else fallback to sentence-transformers
            try:
                ef = embedding_functions.FastEmbedEmbeddingFunction(
                    model_name=os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
                )
            except Exception:
                ef = embedding_functions.DefaultEmbeddingFunction()

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
            return True

        except ImportError:
            print(
                "[VectorDB] chromadb package not found. "
                "Install with: pip install chromadb  "
                "Falling back to legacy in-memory VectorDB."
            )
            return False
        except Exception as e:
            print(f"[VectorDB] ChromaDB init error: {e}. Falling back to legacy VectorDB.")
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    # ΓöÇΓöÇ Indexing ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def add(self, docs: List[Dict], _vectors=None):
        """
        Index *docs* into the Chroma collection.

        *_vectors* is accepted but ignored ΓÇö Chroma generates its own
        dense embeddings.  Pass it for signature compatibility with the
        legacy VectorDB.
        """
        if not self._available or not docs:
            return

        ids, texts, metadatas = [], [], []
        for i, doc in enumerate(docs):
            doc_id = str(doc.get("doc_id") or doc.get("document_id") or f"doc_{i}")
            text = (doc.get("title") or "") + ". " + (doc.get("text") or doc.get("content") or "")

            # Chroma metadata values must be str / int / float / bool
            meta = {
                k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
                for k, v in doc.items()
                if k not in ("text", "content") and v is not None
            }
            # Change 1: ensure product/region are always present as
            # filterable string metadata (used by search_filtered() below).
            meta.setdefault("product", "unknown")
            meta.setdefault("region",  "unknown")

            ids.append(doc_id)
            texts.append(text[:8000])   # Chroma has a ~8k char soft limit per doc
            metadatas.append(meta)

        # Upsert in batches of 500 to avoid memory spikes on large corpora
        batch_size = 500
        for start in range(0, len(ids), batch_size):
            self._collection.upsert(
                ids=ids[start:start + batch_size],
                documents=texts[start:start + batch_size],
                metadatas=metadatas[start:start + batch_size],
            )

    # ΓöÇΓöÇ Retrieval ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Query the Chroma collection.

        Returns a list of result dicts compatible with the RootIQ pipeline:
          {doc, vector_score, layer, doc_id}
        """
        if not self._available or self._collection is None:
            return []

        count = self.count()  # uses TTL cache
        if count == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        ids_list = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        documents_list = results.get("documents", [[]])[0]

        for doc_id, dist, meta, doc_text in zip(ids_list, distances, metadatas_list, documents_list):
            # Chroma returns cosine *distance* (0=identical, 2=opposite)
            # Convert to cosine similarity score in [0, 1]
            similarity = round(max(0.0, 1.0 - dist / 2.0), 4)

            # Reconstruct a doc dict from metadata + document text
            doc = dict(meta)
            doc["doc_id"] = doc_id
            doc["text"] = doc_text

            output.append(
                {
                    "doc": doc,
                    "vector_score": similarity,
                    "layer": doc.get("type") or doc.get("document_type", "unknown"),
                    "doc_id": doc_id,
                }
            )

        return output

    def search_filtered(
        self,
        query: str,
        top_k: int = 5,
        product_filter: Optional[str] = None,
        region_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Change 1: Query the Chroma collection with optional product/region filters.
        Falls back to unfiltered search when product_filter and region_filter are
        both None or 'unknown' (avoids empty result sets on low-coverage datasets).
        """
        if not self._available or self._collection is None:
            return []

        where_clauses = []
        if product_filter and product_filter != "unknown":
            where_clauses.append({"product": {"$eq": product_filter}})
        if region_filter and region_filter != "unknown":
            where_clauses.append({"region": {"$eq": region_filter}})

        if not where_clauses:
            # No useful filters ΓÇö fall back to standard semantic search
            return self.search(query, top_k=top_k)

        where = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]

        count = self.count()  # uses TTL cache
        if count == 0:
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            # If Chroma where-filter returns no results, fall back to unfiltered
            return self.search(query, top_k=top_k)

        output = []
        ids_list      = results.get("ids",       [[]])[0]
        distances     = results.get("distances", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        documents_list = results.get("documents", [[]])[0]

        for doc_id, dist, meta, doc_text in zip(ids_list, distances, metadatas_list, documents_list):
            similarity = round(max(0.0, 1.0 - dist / 2.0), 4)
            doc = dict(meta)
            doc["doc_id"] = doc_id
            doc["text"]   = doc_text
            output.append({
                "doc":          doc,
                "vector_score": similarity,
                "layer":        doc.get("type") or doc.get("document_type", "unknown"),
                "doc_id":       doc_id,
            })

        # If filter returned too few results, supplement with unfiltered
        if len(output) < top_k:
            extra = self.search(query, top_k=top_k)
            seen  = {r["doc_id"] for r in output}
            for r in extra:
                if r["doc_id"] not in seen:
                    output.append(r)
                    seen.add(r["doc_id"])
                if len(output) >= top_k:
                    break

        output.sort(key=lambda r: r["vector_score"], reverse=True)
        return output[:top_k]

    def count(self) -> int:
        """Return number of indexed vectors (TTL-cached for 60 s)."""
        if not self._available or self._collection is None:
            return 0
        import time as _time
        now = _time.time()
        if self._cached_count < 0 or (now - self._cached_count_ts) > self._COUNT_TTL:
            self._cached_count = self._collection.count()
            self._cached_count_ts = now
        return self._cached_count

    def delete_collection(self):
        """Drop the Chroma collection (useful for re-indexing)."""
        if self._available and self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
            except Exception:
                pass


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Layer-Partitioned Chroma Store
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class LayeredVectorDB:
    """
    Layer-partitioned Vector DB.

    Each knowledge layer (analytics_snapshots, issue_clusters, etc.) gets its
    own Chroma collection, preventing a single monolithic index.

    If chromadb is unavailable, falls back to legacy in-memory VectorDB per layer.
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self.layer_stores: Dict[str, Any] = {}

    def _get_or_create(self, layer_name: str) -> "ChromaVectorDB":
        if layer_name not in self.layer_stores:
            collection_name = f"rootiq_{layer_name}"[:63]  # Chroma max name len
            store = ChromaVectorDB(
                collection_name=collection_name,
                persist_dir=self.persist_dir,
            )
            if not store.is_available:
                # Fallback to legacy in-memory
                store = VectorDB()
            self.layer_stores[layer_name] = store
        return self.layer_stores[layer_name]

    def add_layer(self, layer_name: str, docs: List[Dict], vectors=None):
        store = self._get_or_create(layer_name)
        store.add(docs, vectors)

    def search_layers(
        self, query_or_vector, target_layers: List[str], top_k: int = 5
    ) -> List[Dict]:
        """
        Search across selected layers and return top-k merged results.

        *query_or_vector* may be a plain string (used by ChromaVectorDB) or
        a scipy sparse matrix (used by legacy VectorDB).
        """
        results = []
        for layer in target_layers:
            if layer in self.layer_stores:
                store = self.layer_stores[layer]
                if isinstance(store, ChromaVectorDB):
                    layer_res = store.search(str(query_or_vector), top_k=top_k)
                else:
                    layer_res = store.search(query_or_vector, top_k=top_k)
                results.extend(layer_res)

        results.sort(key=lambda r: r["vector_score"], reverse=True)
        return results[:top_k]


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Legacy In-Memory VectorDB (fallback when chromadb is not installed)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class VectorDB:
    """
    Legacy in-memory TF-IDF cosine similarity vector store.
    Used as a fallback when chromadb is not installed.
    """

    def __init__(self):
        self.docs: List[Dict] = []
        self.vectors = None

    def add(self, docs: List[Dict], vectors):
        self.docs = docs
        self.vectors = vectors  # scipy sparse matrix, one row per doc

    def search(self, query_vector, top_k: int = 5) -> List[Dict]:
        if self.vectors is None or self.vectors.shape[0] == 0 or not self.docs:
            return []
        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(query_vector, self.vectors).flatten()
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [
            {
                "doc": self.docs[i],
                "vector_score": round(float(sims[i]), 4),
                "layer": self.docs[i].get("type") or self.docs[i].get("document_type", "unknown"),
                "doc_id": self.docs[i].get("doc_id") or self.docs[i].get("document_id"),
            }
            for i in top_idx
            if sims[i] > 0
        ]

    def count(self) -> int:
        return len(self.docs)

    @property
    def is_available(self) -> bool:
        return True
