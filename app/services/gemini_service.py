import os
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.prompts.system_prompt import SYSTEM_PROMPT

load_dotenv()


class GeminiService:
    """Enhanced Gemini service with retry logic, token tracking, and better error handling."""

    def __init__(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY not found in .env")

            self.client = genai.Client(api_key=api_key)
            
            self.models = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-2.0-flash-lite"
            ]
            
            self.max_retries = 3
            self.retry_delay = 1
            self.max_tokens = 8192
            self.temperature = 0.3
            print("[GeminiService] Initialized successfully")
        except Exception as e:
            print(f"[GeminiService] Initialization error: {str(e)}")
            raise

    def generate_answer(
        self, 
        question: str, 
        context: str = "",
        sources: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate an answer using Gemini with enhanced prompt engineering."""
        try:
            print(f"[GeminiService] Generating answer for: {question[:100]}...")
            
            if not context or context.strip() == "":
                context = "No document context available. Answer using general knowledge only."
                print("[GeminiService] No context provided, using general knowledge")
            else:
                print(f"[GeminiService] Context length: {len(context)} characters")
                print(f"[GeminiService] Sources: {len(sources or [])}")

            prompt = self._build_prompt(question, context, sources or [])
            
            last_error = None
            tokens_used = 0
            model_used = ""

            for model in self.models:
                for attempt in range(self.max_retries):
                    try:
                        print(f"[GeminiService] Trying model: {model}, attempt: {attempt + 1}")
                        
                        response = self.client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=self.temperature,
                                max_output_tokens=self.max_tokens,
                            )
                        )

                        if response.text and response.text.strip():
                            if hasattr(response, 'usage_metadata'):
                                tokens_used = response.usage_metadata.total_token_count
                            model_used = model
                            
                            print(f"[GeminiService] Success with {model} - {len(response.text)} chars")
                            
                            return {
                                "answer": response.text.strip(),
                                "sources": sources or [],
                                "tokens_used": tokens_used,
                                "model_used": model_used
                            }
                        else:
                            raise Exception("Empty response from Gemini")

                    except Exception as e:
                        error_msg = str(e)
                        print(f"[GeminiService] {model} attempt {attempt + 1} failed: {error_msg}")
                        last_error = e
                        
                        if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        elif "busy" in error_msg.lower() or "overloaded" in error_msg.lower():
                            time.sleep(self.retry_delay * 2)
                            continue
                        else:
                            break

            error_msg = "All Gemini models failed"
            if last_error:
                error_msg += f": {str(last_error)}"
            raise Exception(error_msg)
            
        except Exception as e:
            print(f"[GeminiService] Error: {str(e)}")
            raise

    def _build_prompt(self, question: str, context: str, sources: List[Dict]) -> str:
        """Build the complete prompt with source citations."""
        # Add source information to context
        if sources:
            source_text = "\n\n--- SOURCE REFERENCES ---\n"
            for i, source in enumerate(sources, 1):
                metadata = source.get('metadata', {})
                doc_name = metadata.get('document_name', 'Unknown')
                page_num = metadata.get('page', 'N/A')
                source_text += f"[{i}] Document: {doc_name}, Page: {page_num}\n"
            context = context + source_text

        return SYSTEM_PROMPT.format(
            context=context,
            question=question
        )