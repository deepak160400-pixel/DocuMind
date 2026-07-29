from typing import List, Dict, Any, Optional
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore


class Retriever:
    """Enhanced retriever with source tracking and relevance scoring."""

    def __init__(self):
        self.similarity_threshold = 0.25  # Lower threshold for better recall

    def retrieve(
        self, 
        question: str, 
        top_k: int = 10,
        document_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks with metadata."""
        try:
            filter_text = f" (filtered to {document_filter})" if document_filter else ""
            print(f"[RETRIEVER] Searching for: {question[:100]}...{filter_text}")
            
            vector_store = VectorStore()
            loaded = vector_store.load()

            if not loaded:
                print("[RETRIEVER] ❌ No vector store found")
                return []

            print(f"[RETRIEVER] Vector store loaded with {len(vector_store.chunks)} chunks")
            
            if document_filter:
                # Get chunks for this specific document
                doc_chunks = vector_store.get_chunks_by_document(document_filter)
                print(f"[RETRIEVER] Document '{document_filter}' has {len(doc_chunks)} chunks")
                
                if len(doc_chunks) == 0:
                    print(f"[RETRIEVER] ⚠️ No chunks found for document: {document_filter}")
                    return []
                
                # Use only this document's chunks for search
                # We need to build a temporary index or search within filtered results
                query_embedding = EmbeddingService.encode_query(question)
                
                # Get all chunks and filter manually
                all_results = vector_store.search_with_scores(query_embedding, top_k * 2)
                
                # Filter results to only the specified document
                filtered_results = [
                    r for r in all_results 
                    if r.get('metadata', {}).get('document_name') == document_filter
                ]
                
                print(f"[RETRIEVER] Found {len(filtered_results)} results from {document_filter}")
                return filtered_results[:top_k]
            else:
                # Search all documents
                query_embedding = EmbeddingService.encode_query(question)
                results = vector_store.search_with_scores(query_embedding, top_k, document_filter)

                # Filter by similarity threshold
                filtered_results = [
                    r for r in results 
                    if r.get('score', 0) >= self.similarity_threshold
                ]

                if filtered_results:
                    print(f"[RETRIEVER] Found {len(filtered_results)} relevant chunks across all documents")
                else:
                    print("[RETRIEVER] ⚠️ No results passed threshold - returning top results anyway")
                    return results[:top_k]
                
                return filtered_results
                
        except Exception as e:
            print(f"[RETRIEVER ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def retrieve_context(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        """Retrieve and format context with sources."""
        try:
            results = self.retrieve(question, top_k)

            if not results:
                print("[RETRIEVER] No results found - returning empty context")
                return {
                    'context_text': '',
                    'sources': [],
                    'chunks_used': 0
                }

            context_parts = []
            sources = []

            for i, result in enumerate(results, 1):
                text = result.get('text', '')
                metadata = result.get('metadata', {})
                score = result.get('score', 0)

                doc_name = metadata.get('document_name', 'Unknown')
                page = metadata.get('page', 'N/A')
                
                context_parts.append(f"[Source {i}: {doc_name}, Page {page}]\n{text}")

                sources.append({
                    'text': text,
                    'metadata': metadata,
                    'score': score
                })

            context_text = "\n\n---\n\n".join(context_parts)
            
            print(f"[RETRIEVER] Built context from {len(results)} chunks")

            return {
                'context_text': context_text,
                'sources': sources,
                'chunks_used': len(results)
            }
        except Exception as e:
            print(f"[RETRIEVER CONTEXT ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'context_text': '',
                'sources': [],
                'chunks_used': 0
            }