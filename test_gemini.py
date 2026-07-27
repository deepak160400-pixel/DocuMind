from app.services.gemini_service import GeminiService

gemini = GeminiService()

response = gemini.generate_answer(
    "What is Artificial Intelligence?"
)

print("\n")
print("=" * 60)
print(response)
print("=" * 60)