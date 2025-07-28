"""Waldorf architect tool implementation with OpenRouter integration"""
import json
import logging
from typing import Dict, Any, Optional
from httpx import HTTPStatusError, ConnectError, ReadTimeout

from waldorf_config import waldorf_config
from tools.base_architect import BaseArchitect
from prompts.statler_prompts import STATLER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class WaldorfArchitect(BaseArchitect):
    """The nitpicky systems architect powered by OpenRouter"""
    
    def __init__(self):
        super().__init__(waldorf_config)
    
    async def _pre_review_check(self) -> Optional[str]:
        """OpenRouter doesn't require pre-review model checks"""
        # OpenRouter handles model availability automatically
        # and returns appropriate errors if a model is not available
        return None
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Make API call to OpenRouter"""
        url = self.config.get_openrouter_chat_url()
        headers = self.config.get_headers()
        
        payload = {
            "model": self.config.openrouter_model,
            "messages": [
                {"role": "system", "content": STATLER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        logger.debug(f"Calling OpenRouter at {url} with model {self.config.openrouter_model}")
        
        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def _extract_content_from_response(self, response: Dict[str, Any]) -> str:
        """Extract the text content from OpenRouter response format"""
        # OpenRouter uses OpenAI-compatible format
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        
        # Fallback for unexpected format
        logger.warning(f"Unexpected OpenRouter response format: {response.keys()}")
        return str(response)
    
    def _handle_http_error(self, error: HTTPStatusError) -> str:
        """Handle OpenRouter-specific HTTP errors"""
        error_msg = f"OpenRouter returned an error: {error.response.status_code}"
        
        # Handle common OpenRouter error codes
        if error.response.status_code == 401:
            error_msg = "Authentication failed. Check your OPENROUTER_API_KEY"
        elif error.response.status_code == 402:
            error_msg = "Payment required. Check your OpenRouter account balance"
        elif error.response.status_code == 404:
            error_msg = f"Model '{self.config.openrouter_model}' not found. Check available models at openrouter.ai/models"
        elif error.response.status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before trying again"
        elif error.response.status_code == 500:
            error_msg = "OpenRouter server error. The service may be experiencing issues"
        else:
            # Try to parse error message from response
            try:
                error_data = error.response.json()
                if 'error' in error_data:
                    error_details = error_data['error']
                    if isinstance(error_details, dict) and 'message' in error_details:
                        error_msg += f"\n{error_details['message']}"
                    else:
                        error_msg += f"\n{error_details}"
            except:
                error_msg += f"\n{error.response.text[:200]}"
        
        return self._format_error_response(
            error_msg,
            "1. Verify OPENROUTER_API_KEY is correct\n"
            "2. Check your OpenRouter account status\n"
            "3. Try a different model if available"
        )
    
    def _get_timeout_recommendations(self) -> str:
        """Get OpenRouter-specific timeout recommendations"""
        return (
            f"1. Increase OPENROUTER_TIMEOUT environment variable (current: {self.config.openrouter_timeout}s)\n"
            f"2. Use a faster model\n"
            f"3. Check your internet connection"
        )
    
    def _get_connection_recommendations(self) -> str:
        """Get OpenRouter-specific connection recommendations"""
        return (
            f"1. Check your internet connection\n"
            f"2. Verify OPENROUTER_BASE_URL is correct (current: {self.config.openrouter_base_url})\n"
            f"3. Ensure firewall allows HTTPS connections"
        )


async def create_waldorf_architect() -> WaldorfArchitect:
    """Factory function to create a WaldorfArchitect instance"""
    return WaldorfArchitect()