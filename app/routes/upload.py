from flask import Blueprint, request, jsonify
import os
import hashlib
from datetime import datetime
import traceback
from app.services.document_service import DocumentService
from app.rag.chunker import Chunker
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Upload and index a document with accurate page metadata."""
    try:
        print(f"\n{'='*60}")
        print("[UPLOAD] Starting upload process")
        
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "No file selected"
            })

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "success": False,
                "message": "Invalid filename"
            })

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": "Only PDF/PPT/PPTX files are allowed."
            })

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"[UPLOAD] File saved: {filepath}")

        # Extract text with page metadata
        text_data = DocumentService.extract_text_with_metadata(filepath)
        
        if not text_data or not text_data.get('text', '').strip():
            fallback_text = DocumentService.extract_text(filepath)
            if fallback_text.strip():
                text_data = {
                    'text': fallback_text,
                    'pages': [],
                    'total_pages': 0,
                    'metadata': {}
                }
                print("[UPLOAD] Used fallback text extraction")
            else:
                return jsonify({
                    "success": False,
                    "message": "No text found in document. The file might be empty or contain only images."
                })

        extracted_text = text_data.get('text', '')
        print(f"[UPLOAD] Extracted {len(extracted_text)} characters")
        print(f"[UPLOAD] Total pages: {text_data.get('total_pages', 0)}")

        # Generate document hash for uniqueness
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        # Chunk text with accurate page metadata
        chunker = Chunker(chunk_size=500, overlap=100)
        chunks, chunk_metadata = chunker.split_text_with_metadata(
            extracted_text,
            text_data.get('pages', [])
        )

        if len(chunks) == 0:
            return jsonify({
                "success": False,
                "message": "Chunk creation failed. The document might not contain enough text."
            })

        print(f"[UPLOAD] Created {len(chunks)} chunks")

        # Add document name to metadata
        for meta in chunk_metadata:
            meta['document_name'] = file.filename
            if 'page' not in meta or meta['page'] == 'Unknown':
                meta['page'] = 'Unknown'
                meta['page_exact'] = False

        # Generate embeddings
        embeddings = EmbeddingService.encode_chunks(chunks)

        if len(embeddings) == 0:
            return jsonify({
                "success": False,
                "message": "Failed to generate embeddings for the document."
            })

        # Load existing vector store or create new one
        vector_store = VectorStore()
        loaded = vector_store.load()
        
        if loaded:
            print(f"[UPLOAD] Existing vector store loaded with {len(vector_store.chunks)} chunks")
            vector_store.append_embeddings(embeddings, chunks, chunk_metadata)
            print("[UPLOAD] Appended to existing vector store")
        else:
            vector_store.create(embeddings, chunks, chunk_metadata)
            print("[UPLOAD] Created new vector store")
        
        # Add document metadata
        doc_metadata = {
            'document_name': file.filename,
            'file_hash': file_hash,
            'upload_time': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'total_pages': text_data.get('total_pages', 0),
            'total_characters': len(extracted_text),
            'document_metadata': text_data.get('metadata', {})
        }
        vector_store.add_document_metadata(file.filename, doc_metadata)

        # Save updated vector store
        vector_store.save()
        
        total_docs = len(vector_store.documents)
        total_chunks = len(vector_store.chunks)
        print(f"[UPLOAD] Complete! Total documents: {total_docs}, Total chunks: {total_chunks}")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "filename": file.filename,
            "characters": len(extracted_text),
            "chunks": len(chunks),
            "pages": text_data.get('total_pages', 0),
            "message": f"Document '{file.filename}' indexed successfully.",
            "total_documents": total_docs,
            "total_chunks": total_chunks
        })

    except Exception as e:
        print(f"[UPLOAD ERROR] {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Upload failed: {str(e)}"
        })


@upload_bp.route("/documents", methods=["GET"])
def list_documents():
    """List all uploaded documents."""
    try:
        print("[DOCUMENTS] Listing all documents")
        vector_store = VectorStore()
        loaded = vector_store.load()
        
        if not loaded:
            return jsonify({
                "success": True,
                "documents": [],
                "total": 0,
                "total_chunks": 0
            })
        
        documents = vector_store.get_all_documents()
        print(f"[DOCUMENTS] Found {len(documents)} documents, {len(vector_store.chunks)} chunks")
        
        return jsonify({
            "success": True,
            "documents": documents,
            "total": len(documents),
            "total_chunks": len(vector_store.chunks)
        })
        
    except Exception as e:
        print(f"[LIST DOCUMENTS ERROR] {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        })


@upload_bp.route("/clear", methods=["POST"])
def clear_documents():
    """Clear all indexed documents."""
    try:
        print("[CLEAR] Clearing all documents")
        vector_store = VectorStore()
        vector_store.clear()
        
        # Also clear uploads folder
        if os.path.exists(UPLOAD_FOLDER):
            for file in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except:
                    pass
        
        return jsonify({
            "success": True,
            "message": "All documents cleared successfully."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })