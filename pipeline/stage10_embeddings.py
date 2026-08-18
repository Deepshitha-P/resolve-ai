"""
stage10_embeddings.py

Document Chunking + Embedding stage for the RootIQ RAG pipeline.

Chunking  : langchain-text-splitters RecursiveCharacterTextSplitter
            + tiktoken (cl100k_base) for exact BPE token counting.
            Splits at paragraph / sentence / word boundaries so chunks
            are semantically coherent ΓÇö not mid-sentence cuts.

Embeddings: fastembed (BAAI/bge-small-en-v1.5) ΓÇö 100% local, no API key,
            runs via ONNX. ~33MB model download on first run, then cached.
            Outperforms TF-IDF significantly for semantic similarity.

Config (read from .env):
  CHUNK_SIZE    = 500   (BPE tokens, not words)
  CHUNK_OVERLAP = 100   (BPE tokens)
  EMBED_MODEL   = BAAI/bge-small-en-v1.5
"""

import os
from typing import Any, Dict, List, Optional, Tuple

# ΓöÇΓöÇ Load .env ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass

CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 100))
EMBED_MODEL   = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Token-Aware Chunker  (tiktoken + langchain-text-splitters)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def _build_splitter(chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """
    Build a RecursiveCharacterTextSplitter that measures length in BPE tokens
    (tiktoken cl100k_base ΓÇö same encoder as GPT-4 / DeepSeek / most modern LLMs).

    Falls back to character-based splitting if tiktoken is not installed.
    """
    try:
        import tiktoken
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        enc = tiktoken.get_encoding("cl100k_base")

        def _token_len(text: str) -> int:
            return len(enc.encode(text, disallowed_special=()))

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=_token_len,
            # Splits at paragraph ΓåÆ sentence ΓåÆ word boundaries (graceful degradation)
            separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
        )
        return splitter, "tiktoken-cl100k"

    except ImportError:
        # Graceful fallback: character splitter (1 char Γëê 0.25 tokens)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,    # ~4 chars per token
            chunk_overlap=chunk_overlap * 4,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter, "char-fallback"


class TextChunker:
    """
    Token-aware document chunker using langchain-text-splitters + tiktoken.

    Splits text into semantically coherent chunks of `chunk_size` BPE tokens
    with `chunk_overlap` token overlap between consecutive chunks.
    Respects paragraph / sentence / word boundaries ΓÇö no mid-sentence cuts.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter, self._mode = _build_splitter(chunk_size, chunk_overlap)

    def chunk_text(self, text: str) -> List[str]:
        """Split *text* into overlapping chunks. Returns at least one chunk."""
        if not text or not text.strip():
            return [""]
        chunks = self._splitter.split_text(text)
        return chunks if chunks else [text]

    def chunk_document(self, doc: Dict) -> List[Dict]:
        """
        Chunk a single document dict.

        Each output chunk inherits the parent's metadata plus:
          chunk_index   : position within the parent doc
          chunk_total   : total number of chunks from this doc
          parent_doc_id : original doc_id
        """
        text = doc.get("text") or doc.get("content") or ""
        title = doc.get("title") or ""
        chunks_text = self.chunk_text(text)

        result = []
        for i, ct in enumerate(chunks_text):
            chunk = dict(doc)
            chunk["text"]          = ct
            chunk["content"]       = ct
            chunk["title"]         = f"{title} [chunk {i+1}/{len(chunks_text)}]" if len(chunks_text) > 1 else title
            chunk["parent_doc_id"] = doc.get("doc_id") or doc.get("document_id") or ""
            chunk["doc_id"]        = f"{chunk['parent_doc_id']}_chunk{i}"
            chunk["chunk_index"]   = i
            chunk["chunk_total"]   = len(chunks_text)
            result.append(chunk)
        return result

    def chunk_documents(self, docs: List[Dict]) -> List[Dict]:
        """Chunk all docs, returning a flat list of chunk dicts."""
        all_chunks = []
        for doc in docs:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Dense Embedder  (fastembed ΓÇö BAAI/bge-small-en-v1.5)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class FastEmbedder:
    """
    Local dense embedding engine using fastembed (ONNX, no GPU required).

    Model: BAAI/bge-small-en-v1.5  (~33MB, 384-dim, MTEB top-performer)
      - Superior semantic similarity vs TF-IDF for RAG retrieval.
      - Runs entirely offline after the first download (~33MB cached).
      - ~1000 docs/sec on CPU via ONNX Runtime.

    Falls back to TF-IDF Embedder if fastembed is not installed.
    """

    def __init__(self, model_name: str = EMBED_MODEL):
        self.model_name = model_name
        self._model = None
        self._available = False
        self._try_init()

    def _try_init(self):
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
            self._available = True
        except ImportError:
            print("[Embedder] fastembed not installed. Run: pip install fastembed")
        except Exception as e:
            print(f"[Embedder] fastembed init error: {e}. Falling back to TF-IDF.")

    @property
    def is_available(self) -> bool:
        return self._available

    def encode(self, texts: List[str]) -> Any:
        """
        Encode a list of texts into dense vectors.
        Returns a numpy array of shape (n, embedding_dim).
        Falls back to TF-IDF if fastembed unavailable.
        """
        if not self._available or not texts:
            return _tfidf_encode(texts)
        import numpy as np
        embeddings = list(self._model.embed(texts))
        return np.array(embeddings)

    # Alias so it works as a drop-in for the old Embedder
    def fit(self, texts: List[str]) -> "FastEmbedder":
        """No-op ΓÇö fastembed models are pre-trained, no corpus fitting needed."""
        return self

    @property
    def is_fitted(self) -> bool:
        return self._available


# ΓöÇΓöÇ TF-IDF fallback (kept for hybrid BM25 path + when fastembed unavailable)

class Embedder:
    """
    TF-IDF embedder ΓÇö used as fallback and for the BM25 hybrid retrieval path.
    For dense semantic search, FastEmbedder is preferred.
    """

    def __init__(self, max_features: int = 2000):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
        self.is_fitted = False

    def fit(self, texts: List[str]) -> "Embedder":
        if not texts:
            texts = ["empty document"]
        self.vectorizer.fit(texts)
        self.is_fitted = True
        return self

    def encode(self, texts: List[str]):
        if not self.is_fitted:
            raise RuntimeError("Embedder must be fit() before encode().")
        return self.vectorizer.transform(texts)


def _tfidf_encode(texts: List[str]):
    """Quick TF-IDF encode without a pre-fit vectorizer (used as emergency fallback)."""
    emb = Embedder()
    emb.fit(texts)
    return emb.encode(texts)


class LayeredEmbedder:
    """Layer-aware embedder using fastembed per layer."""

    def __init__(self, model_name: str = EMBED_MODEL):
        self.model_name = model_name
        self._global = FastEmbedder(model_name)
        self._layer_embedders: Dict[str, FastEmbedder] = {}

    def fit_layer(self, layer_name: str, docs: List[Dict]) -> "FastEmbedder":
        # All layers share one fastembed model ΓÇö no per-layer fitting needed
        self._layer_embedders[layer_name] = self._global
        return self._global

    def encode_query(self, query: str, layer_name: Optional[str] = None):
        return self._global.encode([query])


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Public API
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def chunk_and_embed_knowledge_memory(
    docs: List[Dict],
    use_llm_chunker: bool = False,  # Single LLM mode ΓÇö rule-based chunker is default
) -> Tuple[List[Dict], FastEmbedder, Any]:
    """
    Chunk documents with tiktoken-aware splitter, then embed with fastembed.

    Steps:
      1. Split each doc into 500-token / 100-overlap chunks
         (measured in real BPE tokens via tiktoken cl100k_base).
      2. Embed all chunks with BAAI/bge-small-en-v1.5 (local ONNX, free).
      3. Return (chunked_docs, embedder, doc_vectors).

    ChromaDB also stores these embeddings independently using the same model
    (configured in stage11_vector_db.py via FastEmbedEmbeddingFunction).
    """
    chunker = TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunked_docs = chunker.chunk_documents(docs)

    embedder = FastEmbedder(model_name=EMBED_MODEL)
    texts = [
        (d.get("title") or "") + ". " + (d.get("text") or d.get("content") or "")
        for d in chunked_docs
    ]
    doc_vectors = embedder.encode(texts)

    return chunked_docs, embedder, doc_vectors


# Backward-compat alias
def embed_knowledge_memory(docs: List[Dict]) -> Tuple[Any, Any]:
    """Legacy entry point. Prefer chunk_and_embed_knowledge_memory()."""
    texts = [
        (d.get("title") or "") + ". " + (d.get("text") or d.get("content") or "")
        for d in docs
    ]
    embedder = FastEmbedder(model_name=EMBED_MODEL)
    return embedder, embedder.encode(texts)
