#!/usr/bin/env python3
"""Waldorf MCP Server - A nitpicky systems architect for code review (OpenRouter powered)"""
import asyncio
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Add parent directory to path for imports
sys.path.insert(0, '.')

from tools.waldorf_architect import create_waldorf_architect, WaldorfArchitect
from waldorf_config import waldorf_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Waldorf MCP")

# Global architect instance
architect: Optional[WaldorfArchitect] = None


@mcp.tool()
async def waldorf_architect(code_or_plan: str, context: str = "") -> str:
    """
    Get a critical review from Waldorf, the nitpicky systems architect.
    
    Waldorf will review your code or architectural plans with a critical eye,
    identifying security vulnerabilities, performance issues, design flaws,
    and suggesting improvements. He's grumpy but helpful!
    
    Args:
        code_or_plan: The code snippet or architectural plan to review
        context: Additional context about what this code/plan does
        
    Returns:
        Detailed critique with specific issues and recommendations
    """
    global architect
    
    try:
        if not architect:
            architect = await create_waldorf_architect()
        
        logger.info(f"Waldorf reviewing {'code' if 'def ' in code_or_plan or 'class ' in code_or_plan else 'plan'}")
        
        # Perform the review
        critique = await architect.review(code_or_plan, context)
        
        return critique
        
    except Exception as e:
        logger.error(f"Error in waldorf_architect: {e}")
        error_msg = f"Waldorf encountered an error: {str(e)}\n\n"
        error_msg += "Make sure:\n"
        error_msg += "1. Your OPENROUTER_API_KEY is set and valid\n"
        error_msg += f"2. The model '{waldorf_config.openrouter_model}' is available on OpenRouter\n"
        error_msg += f"3. You have sufficient credits in your OpenRouter account"
        return error_msg


@mcp.prompt()
def review_prompt() -> str:
    """
    Prompt template for comprehensive code review
    """
    return """Please provide the code or architectural plan you'd like Waldorf to review.

You can use the waldorf_architect tool like this:

```
await waldorf_architect(
    code_or_plan="Your code or plan here",
    context="What this code does or what the plan is for"
)
```

Waldorf will review it for:
- Security vulnerabilities
- Performance issues  
- Design pattern violations
- Error handling gaps
- Edge cases
- Code quality issues
- Architectural concerns

He's nitpicky but constructive!"""


@mcp.resource("waldorf://config")
def get_config() -> str:
    """Get current Waldorf configuration"""
    return f"""Current Waldorf Configuration:
    
OpenRouter API Base: {waldorf_config.openrouter_base_url}
OpenRouter Model: {waldorf_config.openrouter_model}

To change these, set environment variables:
- OPENROUTER_BASE_URL (default: https://openrouter.ai/api/v1)
- OPENROUTER_API_KEY (required)
- OPENROUTER_MCP_MODEL (default: openai/gpt-3.5-turbo)"""


@mcp.resource("waldorf://personality")
def get_personality() -> str:
    """Get Waldorf's personality description"""
    return """Meet Waldorf, Your Nitpicky Systems Architect:

Waldorf is a highly experienced systems architect with decades of experience.
He's known for:

✓ Being extremely detail-oriented
✓ Having strong opinions about code quality
✓ Catching issues others miss
✓ Being grumpy but ultimately helpful
✓ Focusing on security, performance, and maintainability
✓ Valuing simplicity above all else
✓ Being fiercely protective against scope creep

His reviews are thorough and sometimes harsh, but always constructive.
He wants your code to be the best it can be!

"That's the worst code I've seen today... but at least you didn't try to add a blockchain to it." - Waldorf"""


async def cleanup():
    """Cleanup resources on shutdown"""
    global architect
    if architect:
        await architect.client.aclose()
        architect = None


def main():
    """Main entry point"""
    logger.info(f"Starting Waldorf MCP Server...")
    logger.info(f"Configuration: {waldorf_config}")
    
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down Waldorf MCP Server...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        asyncio.run(cleanup())
        sys.exit(1)


if __name__ == "__main__":
    main()