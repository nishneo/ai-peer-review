"""Perplexity API client for making LLM requests."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .config import PERPLEXITY_API_KEY


class PerplexityError:
    """Represents an error from a Perplexity query."""
    def __init__(self, model: str, status_code: int, message: str):
        self.model = model
        self.status_code = status_code
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model': self.model,
            'status_code': self.status_code,
            'message': self.message
        }


async def query_perplexity_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Tuple[Optional[Dict[str, Any]], Optional[PerplexityError]]:
    """
    Query a Perplexity model via the official SDK.

    Args:
        model: Perplexity model identifier (e.g., "perplexity/sonar")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response dict, error). One will be None.
    """
    # Extract actual model name (remove "perplexity/" prefix)
    actual_model = model.replace("perplexity/", "")
    
    try:
        # Import here to avoid issues if SDK not installed
        from perplexity import Perplexity
        
        # Run the synchronous SDK call in a thread pool
        def _call_perplexity():
            client = Perplexity(api_key=PERPLEXITY_API_KEY)
            response = client.chat.completions.create(
                model=actual_model,
                messages=messages
            )
            return response
        
        # Execute with timeout
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, _call_perplexity),
            timeout=timeout
        )
        
        # Extract content from response
        content = response.choices[0].message.content
        
        return {
            'content': content,
            'reasoning_details': None
        }, None

    except asyncio.TimeoutError:
        print(f"Timeout querying Perplexity model {model}")
        return None, PerplexityError(model, 408, f"Request timed out after {timeout}s")
    
    except ImportError as e:
        print(f"Perplexity SDK not installed: {e}")
        return None, PerplexityError(model, 500, "Perplexity SDK not installed. Run: pip install perplexityai")
    
    except Exception as e:
        print(f"Error querying Perplexity model {model}: {e}")
        error_message = str(e)
        status_code = 500
        
        # Try to extract status code from exception if available
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        
        return None, PerplexityError(model, status_code, error_message)

