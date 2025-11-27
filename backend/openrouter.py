"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional, Tuple
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


class ModelError:
    """Represents an error from a model query."""
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


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Tuple[Optional[Dict[str, Any]], Optional[ModelError]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response dict, error). One will be None.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }, None

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_message = str(e)
        
        # Try to get more details from response body
        try:
            error_data = e.response.json()
            if 'error' in error_data:
                error_message = error_data['error'].get('message', str(e))
        except:
            pass
        
        print(f"Error querying model {model}: {e}")
        return None, ModelError(model, status_code, error_message)
    
    except httpx.TimeoutException as e:
        print(f"Timeout querying model {model}: {e}")
        return None, ModelError(model, 408, f"Request timed out after {timeout}s")
    
    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None, ModelError(model, 500, str(e))


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Tuple[Dict[str, Optional[Dict[str, Any]]], List[ModelError]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Tuple of (responses dict, list of errors)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Separate responses and errors
    responses = {}
    errors = []
    
    for model, (response, error) in zip(models, results):
        responses[model] = response
        if error:
            errors.append(error)

    return responses, errors
