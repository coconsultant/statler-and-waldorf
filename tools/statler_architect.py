"""Statler architect tool implementation with Ollama integration"""
import json
import logging
from typing import Dict, Any, Optional
import httpx
from httpx import AsyncClient, HTTPStatusError, ConnectError, ReadTimeout

from statler_config import config
from tools.base_architect import BaseArchitect
from prompts.statler_prompts import STATLER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class StatlerArchitect(BaseArchitect):
    """The nitpicky systems architect powered by Ollama"""
    
    def __init__(self):
        super().__init__(config)
    
    async def check_model_availability(self) -> bool:
        """Check if the configured model is available in Ollama"""
        try:
            url = f"{self.config.ollama_api_base}/api/tags"
            response = await self.client.get(url, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            # Check if our model is in the list (handle versioned names)
            for model_name in model_names:
                if model_name == self.config.ollama_model or model_name.startswith(f"{self.config.ollama_model}:"):
                    logger.info(f"Model '{self.config.ollama_model}' is available")
                    return True
            
            logger.warning(f"Model '{self.config.ollama_model}' not found. Available models: {model_names}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def _pre_review_check(self) -> Optional[str]:
        """Perform Ollama-specific pre-review checks"""
        if not await self.check_model_availability():
            return self._format_error_response(
                f"Model '{self.config.ollama_model}' is not available. "
                f"Pull it with: ollama pull {self.config.ollama_model}",
                "1. Check if Ollama is running\n"
                "2. Verify OLLAMA_API_BASE environment variable\n"
                "3. Ensure the model specified in OLLAMA_MCP_MODEL is available"
            )
        return None
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Ollama"""
        url = self.config.get_ollama_chat_url()
        
        payload = {
            "model": self.config.ollama_model,
            "messages": [
                {"role": "system", "content": STATLER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        logger.debug(f"Calling Ollama at {url} with model {self.config.ollama_model}")
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _extract_content_from_response(self, response: Dict[str, Any]) -> str:
        """Extract the text content from Ollama response format"""
        # Handle different response formats from Ollama chat API
        # When stream=false, the response has a 'message' field
        if 'message' in response and isinstance(response['message'], dict):
            return response['message'].get('content', '')
        # Some versions might have 'response' field instead
        elif 'response' in response:
            return response['response']
        # Fallback to direct content field
        elif 'content' in response:
            return response['content']
        else:
            logger.warning(f"Unexpected response format: {response.keys()}")
            return str(response)
    
    def _handle_http_error(self, error: HTTPStatusError) -> str:
        """Handle Ollama-specific HTTP errors"""
        error_msg = f"Ollama returned an error: {error.response.status_code}"
        if error.response.status_code == 404:
            error_msg += f"\nModel '{self.config.ollama_model}' not found. Pull it with: ollama pull {self.config.ollama_model}"
        else:
            error_msg += f"\n{error.response.text[:200]}"
        
        return self._format_error_response(
            error_msg,
            "1. Check if Ollama is running\n"
            "2. Verify OLLAMA_API_BASE environment variable\n"
            "3. Ensure the model specified in OLLAMA_MCP_MODEL is available"
        )
    
    def _get_timeout_recommendations(self) -> str:
        """Get Ollama-specific timeout recommendations"""
        return (
            f"1. Increase OLLAMA_TIMEOUT environment variable (current: {self.config.ollama_timeout}s)\n"
            f"2. Use a smaller/faster model\n"
            f"3. Ensure the model '{self.config.ollama_model}' is already loaded"
        )
    
    def _get_connection_recommendations(self) -> str:
        """Get Ollama-specific connection recommendations"""
        return (
            f"1. Start Ollama: ollama serve\n"
            f"2. Check OLLAMA_API_BASE is correct (current: {self.config.ollama_api_base})\n"
            f"3. Ensure firewall/network allows connection"
        )


async def create_architect() -> StatlerArchitect:
    """Factory function to create a StatlerArchitect instance"""
    return StatlerArchitect()