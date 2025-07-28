"""Base architect class with shared functionality for Statler and Waldorf"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from httpx import AsyncClient, HTTPStatusError, ConnectError, ReadTimeout

from prompts.statler_prompts import (
    STATLER_SYSTEM_PROMPT,
    CODE_REVIEW_PROMPT_TEMPLATE,
    ARCHITECTURE_REVIEW_PROMPT_TEMPLATE,
    format_critique
)

logger = logging.getLogger(__name__)


class BaseArchitect(ABC):
    """Base class for nitpicky systems architects"""
    
    def __init__(self, config):
        self.config = config
        self.client = AsyncClient(timeout=config.timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def review(self, code_or_plan: str, context: str = "") -> str:
        """
        Review code or architectural plans with a critical eye
        
        Args:
            code_or_plan: The code snippet or architectural plan to review
            context: Additional context about the code/plan
            
        Returns:
            Structured critique from the architect
        """
        try:
            # Perform any provider-specific checks
            check_result = await self._pre_review_check()
            if check_result:
                return check_result
            
            # Determine if this is code or architecture review
            is_code = self._looks_like_code(code_or_plan)
            
            # Prepare the prompt
            if is_code:
                user_prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(
                    code=code_or_plan,
                    context=context or "No additional context provided"
                )
            else:
                user_prompt = ARCHITECTURE_REVIEW_PROMPT_TEMPLATE.format(
                    plan=code_or_plan,
                    context=context or "No additional context provided"
                )
            
            # Call the LLM provider
            response = await self._call_llm(user_prompt)
            
            # Parse and format the response
            critique = self._parse_llm_response(response)
            return format_critique(critique)
            
        except ReadTimeout as e:
            logger.error(f"Timeout waiting for response after {self.config.timeout}s: {e}")
            return self._format_error_response(
                f"Request timed out after {self.config.timeout} seconds",
                self._get_timeout_recommendations()
            )
        except ConnectError as e:
            logger.error(f"Failed to connect to {self.config.api_base_url}: {e}")
            return self._format_error_response(
                f"Cannot connect to {self.config.provider} at {self.config.api_base_url}",
                self._get_connection_recommendations()
            )
        except HTTPStatusError as e:
            logger.error(f"HTTP error from {self.config.provider}: {e}")
            logger.error(f"Response body: {e.response.text}")
            return self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in review: {e}", exc_info=True)
            return self._format_error_response(
                f"An unexpected error occurred: {type(e).__name__}: {str(e)}",
                "1. Check the logs for more details\n"
                f"2. Ensure {self.config.provider} is properly configured\n"
                "3. Try restarting the MCP server"
            )
    
    @abstractmethod
    async def _pre_review_check(self) -> Optional[str]:
        """Perform any provider-specific pre-review checks. Return error message if check fails."""
        pass
    
    @abstractmethod
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Make API call to the LLM provider"""
        pass
    
    def _get_timeout_recommendations(self) -> str:
        """Get timeout error recommendations"""
        return (
            f"1. Increase timeout environment variable\n"
            f"2. Use a faster model\n"
            f"3. Check your connection to {self.config.provider}"
        )
    
    def _get_connection_recommendations(self) -> str:
        """Get connection error recommendations"""
        return (
            f"1. Check if {self.config.provider} service is running\n"
            f"2. Verify the API URL is correct\n"
            f"3. Check firewall/network settings"
        )
    
    @abstractmethod
    def _handle_http_error(self, error: HTTPStatusError) -> str:
        """Handle provider-specific HTTP errors"""
        pass
    
    def _looks_like_code(self, text: str) -> bool:
        """Simple heuristic to determine if input is code or architecture description"""
        code_indicators = [
            'def ', 'class ', 'function ', 'import ', 'from ',
            '{', '}', '()', '=>', 'return ', 'if ', 'for ',
            'const ', 'let ', 'var ', '<?php', 'public ', 'private '
        ]
        
        code_count = sum(1 for indicator in code_indicators if indicator in text)
        return code_count >= 2
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> Dict[str, str]:
        """Parse LLM response into structured critique sections"""
        try:
            # Extract content from response - handle different formats
            content = self._extract_content_from_response(response)
            
            # Initialize sections
            sections = {
                'critical': [],
                'major': [],
                'quality': [],
                'performance': [],
                'security': [],
                'recommendations': [],
                'overall': ''
            }
            
            # Simple parsing based on keywords and sections
            lines = content.split('\n')
            current_section = None
            
            section_keywords = {
                'critical': ['critical', 'severe', 'urgent', 'vulnerability'],
                'major': ['major', 'significant', 'important'],
                'quality': ['quality', 'maintainability', 'readability', 'solid'],
                'performance': ['performance', 'speed', 'efficiency', 'optimization'],
                'security': ['security', 'vulnerability', 'injection', 'authentication'],
                'recommendations': ['recommend', 'suggest', 'should', 'could']
            }
            
            for line in lines:
                line_lower = line.lower()
                
                # Detect section changes
                for section, keywords in section_keywords.items():
                    if any(kw in line_lower for kw in keywords):
                        current_section = section
                        break
                
                # Add content to current section
                if current_section and line.strip():
                    if isinstance(sections[current_section], list):
                        sections[current_section].append(line.strip())
                    else:
                        sections[current_section] += line.strip() + ' '
            
            # Format lists into strings
            for key, value in sections.items():
                if isinstance(value, list):
                    if value:
                        sections[key] = '\n'.join(f"• {item}" for item in value)
                    else:
                        sections[key] = None
            
            # Set overall assessment
            if not sections['overall']:
                severity = "high" if sections['critical'] else "medium" if sections['major'] else "low"
                sections['overall'] = f"Code review complete. Severity level: {severity}. See detailed feedback above."
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                'critical': 'Error parsing AI response',
                'major': str(e),
                'quality': None,
                'performance': None,
                'security': None,
                'recommendations': 'Please try again or check the logs',
                'overall': 'Review failed due to parsing error'
            }
    
    @abstractmethod
    def _extract_content_from_response(self, response: Dict[str, Any]) -> str:
        """Extract the text content from provider-specific response format"""
        pass
    
    def _format_error_response(self, error_message: str, recommendations: str) -> str:
        """Format an error response in the architect's style"""
        return format_critique({
            'critical': f"🔴 {error_message}",
            'major': "Cannot perform review without working LLM connection",
            'quality': None,
            'performance': None,
            'security': None,
            'recommendations': recommendations,
            'overall': "Review failed - fix the connection and try again"
        })