"""
utils_fallbacks.py
------------------
Lightweight fallback embedding utilities for MemeForge AI.
Used when OpenAI embeddings are unavailable or fail.

Order of preference:
1️⃣ SentenceTransformer (HuggingFace local model)
2️⃣ TF-IDF vectorizer (scikit-learn)
"""

from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from src.utils.config import EMBEDDING_MODEL


# ---------- 1️⃣ SentenceTransformer Embeddings ----------
def _embed_st(texts: List[str]):
    """
    Attempt to embed using a local sentence-transformer model.
    Returns np.ndarray or None if model load fails.
    """
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔄 Using local SentenceTransformer: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype="float32")
    except Exception as e:
        print(f"⚠️ SentenceTransformer embedding failed: {e}")
        return None


# ---------- 2️⃣ TF-IDF Embeddings ----------
def _embed_tfidf(texts: List[str]):
    """
    Fallback embedding via TF-IDF + cosine normalization.
    Suitable for lightweight semantic similarity when models unavailable.
    """
    print("🔄 Using TF-IDF fallback for embeddings.")
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=4096)
        mat = vec.fit_transform(texts).astype("float32")
        arr = mat.toarray()
        # Normalize row vectors to unit length
        arr /= (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-10)
        return arr
    except Exception as e:
        print(f"⚠️ TF-IDF embedding error: {e}")
        return np.random.randn(len(texts), 384).astype("float32")  # last-resort fallback


# ---------- 3️⃣ Unified entry ----------
def embed_texts(texts: List[str]):
    """
    Unified embedding interface used across MemeForge agents.
    Returns a 2D float32 numpy array.
    """
    if not texts:
        return np.zeros((0, 384), dtype="float32")

    vecs = _embed_st(texts)
    if vecs is not None:
        return vecs

    # fallback path
    return _embed_tfidf(texts)
