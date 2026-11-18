"""
embedding_service.py - Turn text into "meaning numbers" (embeddings).

Model: sentence-transformers/all-MiniLM-L6-v2
- Runs on your own computer (free, works offline after the first download).
- Turns any text into a list of 384 numbers.
- Texts with similar MEANING get similar numbers, even if they use different words.
- It reads at most 256 tokens (~200 words); longer text is cut off. Our chunks are
  sized (800 characters) so this never happens.

The model is loaded ONCE (it takes a few seconds) and then reused.
"""

import threading

from config import Config

_model = None
_lock = threading.Lock()


def get_model():
    """Load the model the first time it is needed, then reuse it."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(Config.EMBEDDING_MODEL, device="cpu")
    return _model


def embedding_dimension() -> int:
    model = get_model()
    getter = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
    return getter()


def max_tokens() -> int:
    return get_model().max_seq_length


def count_tokens(text: str) -> int:
    """How many tokens the model sees for this text (used to check nothing is cut off)."""
    return len(get_model().tokenizer.encode(text, add_special_tokens=True))


def embed_texts(texts):
    """
    Embed many texts at once (faster than one by one).
    Vectors are normalised to length 1, so cosine similarity = dot product.
    Returns a list of lists of floats.
    """
    if not texts:
        return []
    vectors = get_model().encode(
        list(texts),
        batch_size=Config.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vectors.tolist()


def embed_query(text: str):
    """Embed one search question."""
    return embed_texts([text])[0]
