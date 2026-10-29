from google import genai
from google.genai import types
from app.config import settings
from app.services.circuit_breaker import gemini_breaker
from collections.abc import Iterator

if not settings.GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing.Configure it in your .env file."
    )
client=genai.Client(
    api_key=settings.GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=30_000,
        retry_options=types.HttpRetryOptions(
            attempts=3,
            http_status_codes=[408,429,500,502,503,504],
            initial_delay=1.0,
            exp_base=2.0,
            max_delay=4.0,
            jitter=1.0,
        ),
    ),
)
def is_provider_failure(exc:Exception)->bool:
    retryable_status_codes={408,429,500,502,503,504}
    status_code=getattr(exc,"code",None)
    if status_code in retryable_status_codes:
        return True
    if isinstance(exc,(TimeoutError,ConnectionError)):
        return True
    return False

def generate_response(prompt:str)->tuple[str,int]:
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")
    response=gemini_breaker.call(
        operation=lambda:client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "you are a helpful ai assistant."
                    "give clear,accurate,and concise answers."
                ),
                temperature=0.7,
                max_output_tokens=1024,
            ),
        ),
        is_failure=is_provider_failure,
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    usage=response.usage_metadata
    total_tokens=(
        int(usage.total_token_count)
        if usage and usage.total_token_count is not None 
        else 0
    )
    return response.text,total_tokens 

def stream_response(prompt: str) -> Iterator[tuple[str, int]]:
    """Yield (text_chunk, total_tokens) pairs from Gemini."""

    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    response_stream = client.models.generate_content_stream(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a helpful AI assistant. "
                "Give clear, accurate, and concise answers."
            ),
            temperature=0.7,
            max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        ),
    )

    for chunk in response_stream:
        text_chunk = chunk.text or ""

        usage = getattr(chunk, "usage_metadata", None)
        total_tokens = (
            int(usage.total_token_count)
            if usage and usage.total_token_count is not None
            else 0
        )

        if text_chunk:
            yield text_chunk, total_tokens
