"""Google Gemini API client for making LLM requests."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .config import GOOGLE_API_KEY


class GeminiError:
    """Represents an error from a Gemini query."""
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


async def query_gemini_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Tuple[Optional[Dict[str, Any]], Optional[GeminiError]]:
    """
    Query a Google Gemini model via the official SDK.

    Args:
        model: Gemini model identifier (e.g., "gemini/gemini-2.0-flash")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response dict, error). One will be None.
    """
    # Extract actual model name (remove "gemini/" prefix)
    actual_model = model.replace("gemini/", "")
    
    try:
        # Import here to avoid issues if SDK not installed
        import google.generativeai as genai
        
        # Configure the SDK
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Run the synchronous SDK call in a thread pool
        def _call_gemini():
            gemini_model = genai.GenerativeModel(actual_model)
            
            # Convert messages to Gemini format
            # Gemini uses 'user' and 'model' roles, and expects a different structure
            gemini_history = []
            current_message = None
            
            for msg in messages:
                role = msg['role']
                content = msg['content']
                
                # Map OpenAI-style roles to Gemini roles
                if role == 'assistant':
                    role = 'model'
                elif role == 'system':
                    # Gemini doesn't have a system role, prepend to first user message
                    # or treat as user message
                    role = 'user'
                
                if role == 'user':
                    current_message = content
                    gemini_history.append({'role': 'user', 'parts': [content]})
                else:
                    gemini_history.append({'role': 'model', 'parts': [content]})
            
            # If the last message is from user, we need to generate a response
            if gemini_history and gemini_history[-1]['role'] == 'user':
                # Use chat for multi-turn or generate_content for single turn
                if len(gemini_history) == 1:
                    response = gemini_model.generate_content(current_message)
                else:
                    # Start chat with history (excluding the last user message)
                    chat = gemini_model.start_chat(history=gemini_history[:-1])
                    response = chat.send_message(current_message)
                
                return response.text
            
            return ""
        
        # Execute with timeout
        loop = asyncio.get_event_loop()
        content = await asyncio.wait_for(
            loop.run_in_executor(None, _call_gemini),
            timeout=timeout
        )
        
        return {
            'content': content,
            'reasoning_details': None
        }, None

    except asyncio.TimeoutError:
        print(f"Timeout querying Gemini model {model}")
        return None, GeminiError(model, 408, f"Request timed out after {timeout}s")
    
    except ImportError as e:
        print(f"Google Generative AI SDK not installed: {e}")
        return None, GeminiError(model, 500, "Google Generative AI SDK not installed. Run: pip install google-generativeai")
    
    except Exception as e:
        print(f"Error querying Gemini model {model}: {e}")
        error_message = str(e)
        status_code = 500
        
        # Try to extract status code from exception if available
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        
        return None, GeminiError(model, status_code, error_message)

