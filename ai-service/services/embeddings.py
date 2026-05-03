import logging

logger = logging.getLogger(__name__)

# Global model variable
_model = None

def load_model():
    """Pre-load sentence transformer model at startup."""
    global _model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence-transformers model loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load sentence-transformers: {e}")
        _model = None

def get_model():
    """Return the loaded model."""
    return _model

def encode(texts: list) -> list:
    """Encode texts to embeddings. Returns empty list if model not loaded."""
    if _model is None:
        logger.warning("Model not loaded — skipping encoding.")
        return []
    try:
        embeddings = _model.encode(texts)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Encoding error: {e}")
        return []