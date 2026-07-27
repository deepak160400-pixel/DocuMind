from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore


class Retriever:

    def __init__(self):
        pass

    def retrieve(self, question, top_k=5):

        vector_store = VectorStore()

        loaded = vector_store.load()

        if not loaded:
            return []

        query_embedding = EmbeddingService.encode_query(
            question
        )

        results = vector_store.search(
            query_embedding,
            top_k
        )

        return results