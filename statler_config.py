"""Configuration for Statler MCP Server"""
import logging
import sys
from shared_config import BaseConfig


class Config(BaseConfig):
    """Configuration handler for Statler MCP"""
    
    def __init__(self):
        super().__init__(
            provider="Ollama",
            env_prefix="OLLAMA",
            default_base_url="http://localhost:11434",
            default_model="llama3.2",
            default_timeout=300.0
        )
        
        # Keep compatibility with existing code
        self.ollama_api_base = self.api_base_url
        self.ollama_model = self.model
        self.ollama_timeout = self.timeout
    
    def get_ollama_generate_url(self) -> str:
        """Get the full URL for Ollama generate endpoint"""
        return f"{self.ollama_api_base}/api/generate"
    
    def get_ollama_chat_url(self) -> str:
        """Get the full URL for Ollama chat endpoint"""
        return f"{self.ollama_api_base}/api/chat"


# Global config instance
try:
    config = Config()
except Exception as e:
    logger.error(f"Failed to initialize configuration: {e}")
    sys.exit(1)
