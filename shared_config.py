"""Shared configuration base for MCP servers"""
import os
import logging
import sys

logger = logging.getLogger(__name__)


class BaseConfig:
    """Base configuration with shared logic"""
    
    def __init__(self, provider: str, env_prefix: str, default_base_url: str, 
                 default_model: str, default_timeout: float):
        self.provider = provider
        self.env_prefix = env_prefix
        self.default_base_url = default_base_url
        self.default_model = default_model
        self.default_timeout = default_timeout
        
        # Load configuration
        self.api_base_url = self._get_api_base_url()
        self.model = self._get_model()
        self.timeout = self._get_timeout()
        self._validate_base_config()
    
    def _get_api_base_url(self) -> str:
        """Get API base URL from environment or use default"""
        # Handle different env var names (OLLAMA_API_BASE vs OPENROUTER_BASE_URL)
        env_vars = [
            f"{self.env_prefix}_API_BASE",
            f"{self.env_prefix}_BASE_URL"
        ]
        
        api_base = None
        for var in env_vars:
            api_base = os.environ.get(var)
            if api_base:
                break
        
        if not api_base:
            api_base = self.default_base_url
            
        logger.info(f"Using {self.provider} API base: {api_base}")
        return api_base
    
    def _get_model(self) -> str:
        """Get model from environment or use default"""
        model = os.environ.get(f"{self.env_prefix}_MCP_MODEL", self.default_model)
        logger.info(f"Using {self.provider} model: {model}")
        return model
    
    def _get_timeout(self) -> float:
        """Get timeout from environment or use default"""
        timeout_str = os.environ.get(f"{self.env_prefix}_TIMEOUT", str(self.default_timeout))
        try:
            timeout = float(timeout_str)
            if timeout <= 0:
                logger.warning(f"Invalid {self.env_prefix}_TIMEOUT value: {timeout_str}. Using default: {self.default_timeout}")
                timeout = self.default_timeout
        except ValueError:
            logger.warning(f"Invalid {self.env_prefix}_TIMEOUT value: {timeout_str}. Using default: {self.default_timeout}")
            timeout = self.default_timeout
        logger.info(f"Using {self.provider} timeout: {timeout} seconds")
        return timeout
    
    def _validate_base_config(self) -> None:
        """Validate base configuration"""
        if not self.api_base_url:
            logger.error(f"{self.env_prefix}_API_BASE cannot be empty")
            sys.exit(1)
        
        if not self.model:
            logger.error(f"{self.env_prefix}_MCP_MODEL cannot be empty")
            sys.exit(1)
        
        # Ensure API base doesn't end with slash
        if self.api_base_url.endswith('/'):
            self.api_base_url = self.api_base_url.rstrip('/')
        
        # Validate URL format
        if not (self.api_base_url.startswith('http://') or 
                self.api_base_url.startswith('https://')):
            logger.warning(f"{self.env_prefix}_API_BASE should start with http:// or https://. Got: {self.api_base_url}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(api_base='{self.api_base_url}', model='{self.model}')"