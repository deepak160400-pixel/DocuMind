from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model is None:

            cls._model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        return cls._model

    @classmethod
    def encode_chunks(
        cls,
        chunks
    ):

        model = cls.get_model()

        embeddings = model.encode(

            chunks,

            convert_to_numpy=True,

            normalize_embeddings=True

        )

        return embeddings.astype(np.float32)

    @classmethod
    def encode_query(
        cls,
        query
    ):

        model = cls.get_model()

        embedding = model.encode(

            [query],

            convert_to_numpy=True,

            normalize_embeddings=True

        )

        return embedding.astype(np.float32)