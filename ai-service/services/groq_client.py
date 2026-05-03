import os
import time
import logging
from groq import Groq

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def call_groq(messages: list, temperature: float = 0.3, max_tokens: int = 800) -> str:
    """
    Calls Groq API with 3-retry exponential backoff.
    Returns the response text, or raises RuntimeError after all retries fail.
    """
    last_error = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            wait = 2 ** attempt          # 1s, 2s, 4s
            logger.error(f"Groq attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Groq API unavailable after 3 attempts: {last_error}")