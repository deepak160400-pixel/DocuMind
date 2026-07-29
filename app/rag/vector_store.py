import os
import pickle
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional


class VectorStore:
    """Enhanced vector store with append support for multiple documents."""

    def __init__(self):
        self.index = None
        self.chunks = []
        self.metadata = []
        self.documents = {}

        self.folder = "vector_store"
        self.index_path = os.path.join(self.folder, "index.faiss")
        self.chunk_path = os.path.join(self.folder, "chunks.pkl")
        self.metadata_path = os.path.join(self.folder, "metadata.pkl")
        self.documents_path = os.path.join(self.folder, "documents.json")

    def create(self, embeddings: np.ndarray, chunks: List[str], metadata: List[Dict] = None):
        """Create vector index with metadata."""
        try:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings)
            self.chunks = chunks
            self.metadata = metadata or [{} for _ in chunks]
            print(f"[VECTOR] Created index with {len(chunks)} chunks, dimension={dimension}")
        except Exception as e:
            print(f"[VECTOR CREATE ERROR] {str(e)}")
            raise

    def append_embeddings(self, embeddings: np.ndarray, chunks: List[str], metadata: List[Dict] = None):
        """Append new embeddings to existing index."""
        try:
            if self.index is None:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
            
            self.index.add(embeddings)
            self.chunks.extend(chunks)
            self.metadata.extend(metadata or [{} for _ in chunks])
            print(f"[VECTOR] Appended {len(chunks)} chunks, total: {len(self.chunks)}")
        except Exception as e:
            print(f"[VECTOR APPEND ERROR] {str(e)}")
            raise

    def save(self):
        """Save index, chunks, and metadata."""
        try:
            os.makedirs(self.folder, exist_ok=True)

            faiss.write_index(self.index, self.index_path)

            with open(self.chunk_path, "wb") as f:
                pickle.dump(self.chunks, f)

            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)

            with open(self.documents_path, "w") as f:
                json.dump(self.documents, f, indent=2)
                
            print(f"[VECTOR] Saved {len(self.chunks)} chunks to {self.folder}")
        except Exception as e:
            print(f"[VECTOR SAVE ERROR] {str(e)}")
            raise

    def load(self) -> bool:
        """Load index, chunks, and metadata."""
        try:
            if not os.path.exists(self.index_path):
                print("[VECTOR] No existing index found at", self.index_path)
                return False

            self.index = faiss.read_index(self.index_path)

            with open(self.chunk_path, "rb") as f:
                self.chunks = pickle.load(f)

            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
            else:
                self.metadata = [{} for _ in self.chunks]

            if os.path.exists(self.documents_path):
                with open(self.documents_path, "r") as f:
                    self.documents = json.load(f)

            print(f"[VECTOR] Loaded {len(self.chunks)} chunks, {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"[VECTOR LOAD ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def search_with_scores(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        document_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with similarity scores and metadata.
        """
        try:
            if self.index is None or len(self.chunks) == 0:
                print(f"[VECTOR SEARCH] No index or chunks: index={self.index is not None}, chunks={len(self.chunks)}")
                return []

            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Search for more results than needed
            search_k = min(top_k * 3, len(self.chunks))
            print(f"[VECTOR SEARCH] Searching top {search_k} results from {len(self.chunks)} chunks")
            
            distances, indices = self.index.search(query_embedding, search_k)

            results = []
            seen_texts = set()

            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(self.chunks):
                    continue

                text = self.chunks[idx]
                
                if text in seen_texts:
                    continue
                seen_texts.add(text)

                score = float(distances[0][i])
                meta = self.metadata[idx] if idx < len(self.metadata) else {}

                # Apply document filter if specified
                if document_filter:
                    if meta.get('document_name') != document_filter:
                        continue

                results.append({
                    'text': text,
                    'metadata': meta,
                    'score': score
                })

                if len(results) >= top_k:
                    break

            print(f"[VECTOR SEARCH] Returning {len(results)} results")
            return results
        except Exception as e:
            print(f"[VECTOR SEARCH ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_chunks_by_document(self, doc_name: str) -> List[Dict]:
        """Get all chunks belonging to a specific document."""
        try:
            result = []
            for i, meta in enumerate(self.metadata):
                if meta.get('document_name') == doc_name:
                    result.append({
                        'text': self.chunks[i],
                        'metadata': meta,
                        'index': i
                    })
            print(f"[VECTOR] Found {len(result)} chunks for document: {doc_name}")
            return result
        except Exception as e:
            print(f"[VECTOR GET CHUNKS ERROR] {str(e)}")
            return []

    def add_document_metadata(self, doc_name: str, metadata: Dict):
        """Add or update document metadata."""
        self.documents[doc_name] = metadata
        print(f"[VECTOR] Added document metadata for: {doc_name}")

    def get_document_metadata(self, doc_name: str) -> Optional[Dict]:
        """Get document metadata."""
        return self.documents.get(doc_name)

    def get_all_documents(self) -> List[Dict]:
        """Get all document metadata."""
        return [{'name': name, **meta} for name, meta in self.documents.items()]

    def clear(self):
        """Clear all data."""
        try:
            self.index = None
            self.chunks = []
            self.metadata = []
            self.documents = {}
            
            for path in [self.index_path, self.chunk_path, self.metadata_path, self.documents_path]:
                if os.path.exists(path):
                    os.remove(path)
            
            print("[VECTOR] Cleared all data")
        except Exception as e:
            print(f"[VECTOR CLEAR ERROR] {str(e)}")