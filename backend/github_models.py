"""GitHub Models API client (OpenAI-compatible)."""

import httpx
from typing import List, Dict, Any, Optional, Tuple
from .config import GITHUB_TOKEN

GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"


class GitHubModelsError:
    def __init__(self, model: str, status_code: int, message: str):
        self.model = model
        self.status_code = status_code
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            'model': self.model,
            'status_code': self.status_code,
            'message': self.message,
        }


async def query_github_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> Tuple[Optional[Dict[str, Any]], Optional[GitHubModelsError]]:
    actual_model = model.replace("github/", "", 1)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"model": actual_model, "messages": messages}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(GITHUB_MODELS_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            message = data['choices'][0]['message']
            return {
                'content': message.get('content'),
                'reasoning_details': None,
            }, None

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_message = str(e)
        try:
            body = e.response.json()
            if 'error' in body:
                err = body['error']
                error_message = err.get('message', error_message) if isinstance(err, dict) else str(err)
        except Exception:
            pass
        print(f"Error querying GitHub model {model}: {e} - {error_message}")
        return None, GitHubModelsError(model, status_code, error_message)

    except httpx.TimeoutException:
        return None, GitHubModelsError(model, 408, f"Request timed out after {timeout}s")

    except Exception as e:
        print(f"Error querying GitHub model {model}: {e}")
        return None, GitHubModelsError(model, 500, str(e))
