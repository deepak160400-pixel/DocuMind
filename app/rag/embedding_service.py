from sentence_transformers import SentenceTransformer
import numpy as np
import os


class EmbeddingService:
    """Embedding service with lazy loading and error handling."""

    _model = None
    _model_name = "all-MiniLM-L6-v2"

    @classmethod
    def get_model(cls):
        try:
            if cls._model is None:
                print(f"[EmbeddingService] Loading model: {cls._model_name}")
                cls._model = SentenceTransformer(cls._model_name)
            return cls._model
        except Exception as e:
            print(f"[EmbeddingService] Error loading model: {str(e)}")
            raise

    @classmethod
    def encode_chunks(cls, chunks):
        try:
            if not chunks:
                return np.array([], dtype=np.float32)
            
            model = cls.get_model()
            embeddings = model.encode(
                chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            print(f"[EmbeddingService] Error encoding chunks: {str(e)}")
            raise

    @classmethod
    def encode_query(cls, query):
        try:
            model = cls.get_model()
            embedding = model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"[EmbeddingService] Error encoding query: {str(e)}")
            raise