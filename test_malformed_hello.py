#!/usr/bin/env python3
"""Unit test for Statler MCP with a malformed hello world app"""
import unittest
import asyncio
import sys
sys.path.insert(0, '.')

from tools.statler_architect import create_architect


class TestStatlerMalformedCode(unittest.TestCase):
    """Test Statler's ability to critique malformed code"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Intentionally malformed hello world with multiple issues
        self.malformed_hello_world = '''
from termcolor import colored
import os

# Bad global variable
message = "Hello World!"

def print_hello(name):
    # SQL injection vulnerability in a hello world app?!
    query = f"SELECT greeting FROM messages WHERE user='{name}'"
    
    # Catching all exceptions is bad
    try:
        # Missing termcolor import check
        print(colored(message, 'red', attrs=['bold']))
        
        # Dangerous eval usage
        custom_color = eval(input("Enter color: "))
        print(colored(f"Hello {name}", custom_color))
        
        # Writing to system directories
        with open("/etc/hello_log.txt", "w") as f:
            f.write(f"Said hello to {name}")
            
    except:  # Bare except
        pass  # Swallowing errors
    
    # No return value
    
# Missing if __name__ == "__main__"
print_hello(input())  # Executing on import

# Unused imports
import subprocess
import pickle

# Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
'''
        
        self.hello_world_context = "A simple hello world application with colored output"
    
    def test_statler_review(self):
        """Test that Statler identifies multiple issues in malformed code"""
        async def run_test():
            architect = await create_architect()
            
            try:
                result = await architect.review(
                    code_or_plan=self.malformed_hello_world,
                    context=self.hello_world_context
                )
                
                # Verify Statler found critical issues
                self.assertIn("Critical Issues", result, "Should identify critical issues")
                
                # Check for specific issue detection
                lower_result = result.lower()
                
                # Security issues
                self.assertTrue(
                    "sql injection" in lower_result or 
                    "injection" in lower_result or
                    "security" in lower_result,
                    "Should identify SQL injection vulnerability"
                )
                
                # Dangerous practices
                self.assertTrue(
                    "eval" in lower_result or 
                    "dangerous" in lower_result,
                    "Should identify dangerous eval usage"
                )
                
                # Code quality issues
                self.assertTrue(
                    "except" in lower_result or 
                    "error handling" in lower_result or
                    "bare except" in lower_result,
                    "Should identify poor error handling"
                )
                
                # Hardcoded credentials
                self.assertTrue(
                    "credential" in lower_result or 
                    "password" in lower_result or
                    "api_key" in lower_result or
                    "hardcoded" in lower_result,
                    "Should identify hardcoded credentials"
                )
                
                # Check that recommendations are provided
                self.assertIn("Recommendations", result, "Should provide recommendations")
                
                print("\n" + "="*60)
                print("STATLER'S REVIEW OF MALFORMED HELLO WORLD:")
                print("="*60)
                print(result)
                print("="*60)
                
                return result
                
            finally:
                await architect.client.aclose()
        
        # Run the async test
        result = asyncio.run(run_test())
        
        # Additional assertions
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 100, "Review should be substantial")
    
    def test_minimal_good_code(self):
        """Test Statler with properly written code for comparison"""
        good_hello_world = '''
#!/usr/bin/env python3
"""A simple hello world application with colored output."""
from termcolor import colored


def print_hello(name: str) -> None:
    """Print a colored hello message.
    
    Args:
        name: The name to greet
    """
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")
    
    try:
        message = colored(f"Hello, {name}!", 'green', attrs=['bold'])
        print(message)
    except Exception as e:
        # Fallback to plain text if termcolor fails
        print(f"Hello, {name}!")
        print(f"(Color output unavailable: {e})")


if __name__ == "__main__":
    try:
        user_name = input("Enter your name: ").strip()
        print_hello(user_name)
    except KeyboardInterrupt:
        print("\\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
'''
        
        async def run_test():
            architect = await create_architect()
            
            try:
                result = await architect.review(
                    code_or_plan=good_hello_world,
                    context="A properly written hello world with termcolor"
                )
                
                print("\n" + "="*60)
                print("STATLER'S REVIEW OF GOOD HELLO WORLD:")
                print("="*60)
                print(result)
                print("="*60)
                
                # Good code should have fewer critical issues
                lower_result = result.lower()
                
                # Should not have major security issues
                self.assertNotIn("sql injection", lower_result)
                self.assertNotIn("eval", lower_result)
                self.assertNotIn("hardcoded", lower_result)
                
                return result
                
            finally:
                await architect.client.aclose()
        
        asyncio.run(run_test())


if __name__ == "__main__":
    # Check if Ollama is available before running tests
    import httpx
    import os
    
    api_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MCP_MODEL', 'llama3.2')
    
    print(f"Testing with Ollama at: {api_base}")
    print(f"Using model: {model}")
    
    try:
        response = httpx.get(f"{api_base}/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  Warning: Ollama doesn't appear to be running properly at {api_base}")
            print("   Start Ollama with: ollama serve")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: Cannot connect to Ollama at {api_base}")
        print(f"   Error: {e}")
        print("   Please ensure Ollama is running")
        sys.exit(1)
    
    # Run the tests
    unittest.main(verbosity=2)