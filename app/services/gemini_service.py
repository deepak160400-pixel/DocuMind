import os

from dotenv import load_dotenv
from google import genai

from app.prompts.system_prompt import SYSTEM_PROMPT

load_dotenv()


class GeminiService:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise Exception("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)

        # Model fallback list (tries next if one is busy)
        self.models = [

            "gemini-2.5-flash",

            "gemini-2.0-flash",

            "gemini-flash-latest",

            "gemini-2.0-flash-lite"

        ]

    def generate_answer(self, question, context=""):

        prompt = SYSTEM_PROMPT.format(

            context=context,

            question=question

        )

        last_error = None

        for model in self.models:

            try:

                response = self.client.models.generate_content(

                    model=model,

                    contents=prompt

                )

                if response.text:

                    return response.text

            except Exception as e:

                print(f"[Gemini] {model} failed : {e}")

                last_error = e

                continue

        if last_error:

            raise Exception(

                f"All Gemini models failed.\n\n{last_error}"

            )

        raise Exception("Unable to generate response.")