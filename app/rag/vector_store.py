import os
import pickle
import faiss
import numpy as np


class VectorStore:

    def __init__(self):

        self.index = None
        self.chunks = []

        self.folder = "vector_store"

        self.index_path = os.path.join(
            self.folder,
            "index.faiss"
        )

        self.chunk_path = os.path.join(
            self.folder,
            "chunks.pkl"
        )

    def create(self, embeddings, chunks):

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)

        self.chunks = chunks

    def save(self):

        os.makedirs(
            self.folder,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            self.index_path
        )

        with open(
            self.chunk_path,
            "wb"
        ) as file:

            pickle.dump(
                self.chunks,
                file
            )

    def load(self):

        if not os.path.exists(self.index_path):

            return False

        self.index = faiss.read_index(
            self.index_path
        )

        with open(
            self.chunk_path,
            "rb"
        ) as file:

            self.chunks = pickle.load(file)

        return True

    def search(
        self,
        query_embedding,
        top_k=5
    ):

        if self.index is None:

            return []

        distances, indices = self.index.search(

            query_embedding,

            top_k

        )

        results = []

        for index in indices[0]:

            if index != -1:

                results.append(

                    self.chunks[index]

                )

        return results