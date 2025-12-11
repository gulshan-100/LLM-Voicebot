from dotenv import load_dotenv, find_dotenv
import os
import httpx

load_dotenv(find_dotenv())

try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError(f"openai package is required for llm.py: {e}")

# Persistent HTTP client with connection pooling for lower latency
_http_client = None

def _get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            http2=True  # HTTP/2 for multiplexing
        )
    return _http_client


def _get_openai_client():
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY not found in environment')
    return OpenAI(api_key=api_key, http_client=_get_http_client())


def generate_llm_response(text: str) -> str:
    """Generate a concise response using the new OpenAI client.

    Uses `OPENAI_API_KEY` and `OPENAI_MODEL` (defaults to `gpt-4o-mini` for speed).
    Raises RuntimeError on configuration or invocation failures.
    """
    client = _get_openai_client()
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')  # Much faster than gpt-4o

    system_prompt = 'You are a helpful assistant. Answer very concisely in 1-2 sentences.'
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': text},
    ]

    try:
        resp = client.chat.completions.create(
            model=model, 
            messages=messages, 
            max_tokens=100,  # Reduced for faster response
            temperature=0.3,  # Lower for faster, more deterministic output
            timeout=5  # 5 second timeout
        )
    except Exception as e:
        raise RuntimeError(f"LLM invocation failed: {e}")

    # Try to extract the assistant content robustly
    try:
        choice = resp.choices[0]
        message = choice.message
        content = getattr(message, 'content', None) or (message.get('content') if hasattr(message, 'get') else None)
        if content:
            return content.strip()
        else:
            return ''
    except Exception:
        return ''


def stream_llm_response(text: str):
    """Stream LLM tokens from OpenAI ChatCompletion (stream=True).

    Yields individual token strings as they arrive. If the OpenAI client
    doesn't support streaming or streaming fails, falls back to yielding
    the whole response as a single chunk.
    """
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')  # Much faster than gpt-4o

    system_prompt = 'You are a helpful assistant. Answer very concisely in 1-2 sentences.'
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': text},
    ]

    client = _get_openai_client()
    try:
        for chunk in client.chat.completions.create(
            model=model, 
            messages=messages, 
            stream=True, 
            temperature=0.3,  # Lower for faster output
            max_tokens=100,  # Reduced for faster response
            timeout=10
        ):
            try:
                # chunk is likely an object with choices list
                choices = getattr(chunk, 'choices', None) or (chunk.get('choices') if isinstance(chunk, dict) else None)
                if not choices:
                    continue
                choice0 = choices[0]
                # delta may be present as mapping
                delta = None
                if isinstance(choice0, dict):
                    delta = choice0.get('delta')
                else:
                    delta = getattr(choice0, 'delta', None)
                if not delta:
                    continue
                # content in delta
                content = getattr(delta, 'content', None) or (delta.get('content') if hasattr(delta, 'get') else None)
                if content:
                    yield content
            except Exception:
                continue
    except Exception:
        # streaming failed; fall back to non-streaming call
        try:
            full = generate_llm_response(text)
            yield full
        except Exception as e:
            raise RuntimeError(f"LLM streaming failed and fallback also failed: {e}")

