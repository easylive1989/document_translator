import os
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

class GeminiClient:
    def __init__(self, model_name: str = "flash"):
        """
        Initialize the Gemini Client.

        Args:
            model_name (str): "flash" or "pro". Defaults to "flash".
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")

        genai.configure(api_key=api_key)

        # Map friendly names to actual model names
        self.model_map = {
            "flash": "gemini-2.0-flash",
            "pro": "gemini-2.5-pro"
        }

        target_model = self.model_map.get(model_name.lower(), model_name)
        self.model = genai.GenerativeModel(target_model)

    @retry(
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(20)
    )
    def translate_text(self, text: str, target_lang: str = "Traditional Chinese") -> str:
        """
        Translates text to the target language.

        Args:
            text (str): Text to translate.
            target_lang (str): Target language.

        Returns:
            str: Translated text.
        """
        if not text or not text.strip():
            return text

        prompt = (
            f"Translate the following text into {target_lang}. "
            "Maintain the original tone and style. "
            "Do not add any explanations or extra text. "
            "Just provide the translation.\n\n"
            f"Text: {text}"
        )

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            # If safety settings block it or other errors occur, we might want to log it
            # For now, let tenacity handle transient errors, but re-raise others
            raise e
