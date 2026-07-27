from flask import Blueprint
from flask import request
from flask import jsonify

import os

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

    filepath = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(filepath)

    # -----------------------------
    # Extract Text
    # -----------------------------

    text = DocumentService.extract_text(filepath)

    if not text.strip():

        return jsonify({
            "success": False,
            "message": "No text found in document."
        })

    # -----------------------------
    # Chunk Text
    # -----------------------------

    chunker = Chunker()

    chunks = chunker.split_text(text)

    if len(chunks) == 0:

        return jsonify({
            "success": False,
            "message": "Chunk creation failed."
        })

    # -----------------------------
    # Embeddings
    # -----------------------------

    embeddings = EmbeddingService.encode_chunks(chunks)

    # -----------------------------
    # Build Vector Store
    # -----------------------------

    vector_store = VectorStore()

    vector_store.create(
        embeddings,
        chunks
    )

    vector_store.save()

    return jsonify({

        "success": True,

        "filename": file.filename,

        "characters": len(text),

        "chunks": len(chunks),

        "message": "Document indexed successfully."

    })