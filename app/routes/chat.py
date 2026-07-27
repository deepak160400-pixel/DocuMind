from flask import Blueprint
from flask import request
from flask import jsonify

from app.services.gemini_service import GeminiService
from app.rag.retriever import Retriever

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():

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

    try:

        retriever = Retriever()

        chunks = retriever.retrieve(
            question,
            top_k=5
        )

        context = "\n\n".join(chunks)

        gemini = GeminiService()

        answer = gemini.generate_answer(
            question=question,
            context=context
        )

        return jsonify({

            "success": True,

            "answer": answer,

            "chunks_used": len(chunks)

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        })