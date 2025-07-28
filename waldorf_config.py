"""Configuration for Waldorf MCP Server (OpenRouter integration)"""
import os
import sys
import logging
from shared_config import BaseConfig

logger = logging.getLogger(__name__)


class WaldorfConfig(BaseConfig):
    """Configuration handler for Waldorf MCP (OpenRouter)"""
    
    def __init__(self):
        super().__init__(
            provider="OpenRouter",
            env_prefix="OPENROUTER",
            default_base_url="https://openrouter.ai/api/v1",
            default_model="openai/gpt-3.5-turbo",
            default_timeout=60.0
        )
        
        # OpenRouter-specific: API key
        self.openrouter_api_key = self._get_openrouter_api_key()
        self._validate_api_key()
        
        # Keep compatibility with existing code
        self.openrouter_base_url = self.api_base_url
        self.openrouter_model = self.model
        self.openrouter_timeout = self.timeout
    
    def _get_openrouter_api_key(self) -> str:
        """Get OpenRouter API key from environment"""
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if api_key:
            logger.info("OpenRouter API key configured")
        else:
            logger.error("OPENROUTER_API_KEY environment variable not set")
        return api_key
    
    def _validate_api_key(self) -> None:
        """Validate API key is present"""
        if not self.openrouter_api_key:
            logger.error("OPENROUTER_API_KEY is required for OpenRouter API access")
            sys.exit(1)
    
    def get_openrouter_chat_url(self) -> str:
        """Get the full URL for OpenRouter chat completions endpoint"""
        return f"{self.openrouter_base_url}/chat/completions"
    
    def get_headers(self) -> dict:
        """Get headers for OpenRouter API requests"""
        return {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/statler",
            "X-Title": "Waldorf MCP Code Review"
        }


# Global config instance
try:
    waldorf_config = WaldorfConfig()
except Exception as e:
    logger.error(f"Failed to initialize Waldorf configuration: {e}")
    sys.exit(1)