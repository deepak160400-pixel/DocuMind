from flask import Blueprint, request, jsonify
import traceback
import re
from app.services.gemini_service import GeminiService
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore

chat_bp = Blueprint("chat", __name__)


def detect_document_mention(question: str, documents: list) -> str:
    """
    Detect which document the user is referring to in their question.
    
    Returns:
        str: Document name if found, else None
    """
    if not documents:
        return None
    
    question_lower = question.lower()
    
    # Check if user mentions a specific document
    for doc in documents:
        doc_name = doc.get('name', '')
        doc_name_lower = doc_name.lower()
        
        # Check for exact or partial match
        # Remove extension for matching
        doc_name_no_ext = doc_name_lower.rsplit('.', 1)[0] if '.' in doc_name_lower else doc_name_lower
        
        # Various ways user might mention the document
        patterns = [
            doc_name_lower,  # Full name
            doc_name_no_ext,  # Without extension
            doc_name_no_ext.replace('_', ' '),  # With spaces instead of underscores
            doc_name_no_ext.replace('-', ' '),  # With spaces instead of hyphens
        ]
        
        for pattern in patterns:
            if pattern and pattern in question_lower:
                print(f"[CHAT] Detected document mention: {doc_name}")
                return doc_name
    
    # Check if user says "this document" or "the document" - use first one
    if any(word in question_lower for word in ['this document', 'the document', 'uploaded document']):
        print(f"[CHAT] Using default document: {documents[0].get('name')}")
        return documents[0].get('name')
    
    return None


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Process chat request with intelligent document filtering."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received."
            })

        question = data.get("message", "").strip()

        if question == "":
            return jsonify({
                "success": False,
                "message": "Please enter a question."
            })

        print(f"\n{'='*60}")
        print(f"[CHAT] Question: {question}")
        print(f"{'='*60}")

        # Get all documents
        vector_store = VectorStore()
        loaded = vector_store.load()
        
        if not loaded:
            print("[CHAT] No vector store found")
            return jsonify({
                "success": False,
                "message": "No documents uploaded. Please upload a document first."
            })

        all_documents = vector_store.get_all_documents()
        print(f"[CHAT] Available documents: {[d['name'] for d in all_documents]}")

        # Detect which document the user is asking about
        detected_doc = detect_document_mention(question, all_documents)
        
        if detected_doc:
            print(f"[CHAT] 🎯 Filtering to document: {detected_doc}")
        else:
            print("[CHAT] 🌐 No specific document detected - searching all documents")

        # Retrieve chunks with optional document filter
        retriever = Retriever()
        
        if detected_doc:
            # Search only in the detected document
            results = retriever.retrieve(question, top_k=10, document_filter=detected_doc)
        else:
            # Search all documents
            results = retriever.retrieve(question, top_k=10)
            # If no results, try without threshold
            if not results:
                retriever.similarity_threshold = 0.1
                results = retriever.retrieve(question, top_k=10)

        # Build context from results
        if not results:
            print("[CHAT] No results found")
            context = "No relevant context found in the uploaded documents."
            sources = []
            chunks_used = 0
        else:
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
            
            context = "\n\n---\n\n".join(context_parts)
            chunks_used = len(results)
            print(f"[CHAT] Built context from {chunks_used} chunks")

        # Generate answer with Gemini
        gemini = GeminiService()
        result = gemini.generate_answer(
            question=question,
            context=context,
            sources=sources
        )

        # Format sources for frontend
        formatted_sources = []
        for source in result.get('sources', []):
            metadata = source.get('metadata', {})
            page = metadata.get('page', 'Unknown')
            page_exact = metadata.get('page_exact', False)
            
            page_display = f"Page {page}" if page != 'Unknown' else 'Unknown'
            if not page_exact and page != 'Unknown':
                page_display += " (estimated)"
            
            formatted_sources.append({
                'text': source.get('text', ''),
                'metadata': {
                    'document_name': metadata.get('document_name', 'Unknown'),
                    'page': page,
                    'page_display': page_display,
                    'page_exact': page_exact
                },
                'score': source.get('score', 0)
            })

        response = {
            "success": True,
            "answer": result['answer'],
            "chunks_used": chunks_used,
            "sources": formatted_sources,
            "tokens_used": result.get('tokens_used', 0),
            "model_used": result.get('model_used', 'Unknown'),
            "context_used": bool(chunks_used > 0),
            "detected_document": detected_doc,
            "total_documents": len(all_documents)
        }

        print(f"[CHAT] Response sent - chunks: {chunks_used}, detected: {detected_doc}")
        print(f"{'='*60}\n")

        return jsonify(response)

    except Exception as e:
        print(f"[CHAT ERROR] {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Failed to generate response: {str(e)}"
        })