#!/usr/bin/env python3
"""Statler MCP Server - A nitpicky systems architect for code review"""
import asyncio
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Add parent directory to path for imports
sys.path.insert(0, '.')

from tools.statler_architect import create_architect, StatlerArchitect
from statler_config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Statler MCP")

# Global architect instance
architect: Optional[StatlerArchitect] = None


@mcp.tool()
async def statler_architect(code_or_plan: str, context: str = "") -> str:
    """
    Get a critical review from Statler, the nitpicky systems architect.
    
    Statler will review your code or architectural plans with a critical eye,
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
            architect = await create_architect()
        
        logger.info(f"Statler reviewing {'code' if 'def ' in code_or_plan or 'class ' in code_or_plan else 'plan'}")
        
        # Perform the review
        critique = await architect.review(code_or_plan, context)
        
        return critique
        
    except Exception as e:
        logger.error(f"Error in statler_architect: {e}")
        error_msg = f"Statler encountered an error: {str(e)}\n\n"
        error_msg += "Make sure:\n"
        error_msg += "1. Ollama is running (check with 'ollama list')\n"
        error_msg += f"2. The model '{config.ollama_model}' is available\n"
        error_msg += f"3. Ollama API is accessible at {config.ollama_api_base}"
        return error_msg


@mcp.prompt()
def review_prompt() -> str:
    """
    Prompt template for comprehensive code review
    """
    return """Please provide the code or architectural plan you'd like Statler to review.

You can use the statler_architect tool like this:

```
await statler_architect(
    code_or_plan="Your code or plan here",
    context="What this code does or what the plan is for"
)
```

Statler will review it for:
- Security vulnerabilities
- Performance issues  
- Design pattern violations
- Error handling gaps
- Edge cases
- Code quality issues
- Architectural concerns

He's nitpicky but constructive!"""


@mcp.resource("statler://config")
def get_config() -> str:
    """Get current Statler configuration"""
    return f"""Current Statler Configuration:
    
Ollama API Base: {config.ollama_api_base}
Ollama Model: {config.ollama_model}

To change these, set environment variables:
- OLLAMA_API_BASE (default: http://localhost:11434)
- OLLAMA_MCP_MODEL (default: llama3.2)"""


@mcp.resource("statler://personality")
def get_personality() -> str:
    """Get Statler's personality description"""
    return """Meet Statler, Your Nitpicky Systems Architect:

Statler is a highly experienced systems architect with decades of experience.
He's known for:

✓ Being extremely detail-oriented
✓ Having strong opinions about code quality
✓ Catching issues others miss
✓ Being grumpy but ultimately helpful
✓ Focusing on security, performance, and maintainability

His reviews are thorough and sometimes harsh, but always constructive.
He wants your code to be the best it can be!

"That's the worst code I've seen today... but I've seen worse." - Statler"""


async def cleanup():
    """Cleanup resources on shutdown"""
    global architect
    if architect:
        await architect.client.aclose()
        architect = None


def main():
    """Main entry point"""
    logger.info(f"Starting Statler MCP Server...")
    logger.info(f"Configuration: {config}")
    
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down Statler MCP Server...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        asyncio.run(cleanup())
        sys.exit(1)


if __name__ == "__main__":
    main()