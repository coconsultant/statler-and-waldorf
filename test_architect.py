#!/usr/bin/env python3
"""Unified test for Statler & Waldorf MCP architects"""
import unittest
import asyncio
import sys
import os
import time
from termcolor import colored
from typing import Optional, Tuple

# Add current directory to path
sys.path.insert(0, '.')


class ArchitectDetector:
    """Detects and selects the appropriate architect based on environment"""
    
    @staticmethod
    def detect() -> Tuple[str, Optional[object]]:
        """
        Detect which architect to use based on environment variables.
        Returns: (architect_name, architect_module)
        """
        # Check for Waldorf (OpenRouter) first
        if os.environ.get('OPENROUTER_API_KEY'):
            try:
                from tools.waldorf_architect import create_waldorf_architect
                return ("Waldorf (OpenRouter)", create_waldorf_architect)
            except ImportError as e:
                print(colored(f"❌ Failed to import Waldorf: {e}", "red"))
        
        # Check for Statler (Ollama)
        ollama_base = os.environ.get('OLLAMA_API_BASE', 'http://localhost:11434')
        if ollama_base:
            try:
                from tools.statler_architect import create_architect
                return ("Statler (Ollama)", create_architect)
            except ImportError as e:
                print(colored(f"❌ Failed to import Statler: {e}", "red"))
        
        return ("None", None)


class TestArchitect(unittest.TestCase):
    """Test the architect's ability to critique malformed code"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Focused malformed code sample (security issues only)
        self.malformed_code = '''
import os
import subprocess

# Hardcoded credentials (security issue)
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

def process_user_input(user_input):
    """Process user commands - UNSAFE"""
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name='{user_input}'"
    
    # Command injection vulnerability
    result = subprocess.run(f"echo {user_input}", shell=True, capture_output=True)
    
    # Dangerous eval usage
    if user_input.startswith("calc:"):
        return eval(user_input[5:])
    
    # Path traversal vulnerability
    with open(f"/data/{user_input}.txt", "r") as f:
        return f.read()

# Missing input validation
password = input("Enter password: ")
if password == DB_PASSWORD:  # Comparing plaintext password
    print("Access granted")

# Insecure random for tokens
import random
token = random.randint(1000, 9999)  # Predictable token generation
'''
        
        self.context = "Security audit for a user input processing module"
        
        # Detect which architect to use
        self.architect_name, self.architect_factory = ArchitectDetector.detect()
    
    def test_architect_review(self):
        """Test that the architect identifies security issues"""
        if not self.architect_factory:
            self.skipTest(colored(
                f"⚠️  No architect available. Set OPENROUTER_API_KEY for Waldorf "
                f"or ensure Ollama is running for Statler", "yellow"
            ))
        
        # Check if we're in demo mode
        if os.environ.get('DEMO_MODE'):
            self._run_demo_mode()
            return
        
        print(colored(f"\n🎭 Testing with {self.architect_name}", "cyan", attrs=['bold']))
        print(colored("=" * 60, "cyan"))
        
        async def run_review():
            start_time = time.perf_counter()
            architect = None
            
            try:
                # Create architect instance
                print(colored("⏳ Initializing architect...", "yellow"))
                architect = await self.architect_factory()
                
                # Run review with timeout
                print(colored("🔍 Running security review...", "yellow"))
                result = await asyncio.wait_for(
                    architect.review(
                        code_or_plan=self.malformed_code,
                        context=self.context
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                elapsed = time.perf_counter() - start_time
                print(colored(f"✅ Review completed in {elapsed:.1f}s", "green"))
                
                return result, elapsed
                
            except asyncio.TimeoutError:
                elapsed = time.perf_counter() - start_time
                print(colored(f"\n⚠️  Review timed out after {elapsed:.1f}s", "yellow"))
                print(colored("This might mean:", "yellow"))
                print(colored("  • The LLM service is slow or overloaded", "yellow"))
                print(colored("  • The model is still loading", "yellow"))
                print(colored("  • Network connectivity issues", "yellow"))
                print(colored("\nTry:", "cyan"))
                print(colored("  • Running with DEMO_MODE=1 for a quick test", "cyan"))
                print(colored("  • Increasing timeout in the test", "cyan"))
                print(colored("  • Using a smaller/faster model", "cyan"))
                self.fail(colored(f"Review timed out after {elapsed:.1f}s", "red"))
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                error_type = type(e).__name__
                print(colored(f"\n❌ {error_type}: {str(e)}", "red"))
                print(colored(f"Failed after {elapsed:.1f}s", "red"))
                self.fail(f"Review failed: {e}")
            finally:
                if architect and hasattr(architect, 'client'):
                    await architect.client.aclose()
        
        # Run the async review
        result, elapsed = asyncio.run(run_review())
        
        # Verify results
        self._verify_review_results(result)
        
        # Display summary
        self._display_summary(result, elapsed)
    
    def _verify_review_results(self, result: str):
        """Verify the review caught the security issues"""
        print(colored("\n📋 Verifying detection of security issues:", "blue"))
        
        checks = [
            ("SQL Injection", ["sql injection", "injection", "query"]),
            ("Command Injection", ["command injection", "subprocess", "shell=true"]),
            ("Eval Usage", ["eval", "dangerous"]),
            ("Hardcoded Credentials", ["credential", "password", "api_key", "hardcoded"]),
            ("Path Traversal", ["path traversal", "directory traversal", "file access"]),
        ]
        
        lower_result = result.lower()
        passed = 0
        
        for issue_name, keywords in checks:
            found = any(keyword in lower_result for keyword in keywords)
            if found:
                print(colored(f"  ✓ {issue_name}", "green"))
                passed += 1
            else:
                print(colored(f"  ✗ {issue_name}", "red"))
        
        # Assert that at least 4 out of 5 issues were found
        self.assertGreaterEqual(
            passed, 4,
            f"Expected at least 4 security issues to be detected, but only {passed} were found"
        )
        
        # Check for critical issues section
        self.assertIn("Critical Issues", result, "Should have a Critical Issues section")
        
        # Check for recommendations
        self.assertIn("Recommendations", result, "Should provide recommendations")
    
    def _display_summary(self, result: str, elapsed: float):
        """Display a summary of the review"""
        print(colored("\n📊 Review Summary", "magenta", attrs=['bold']))
        print(colored("=" * 60, "magenta"))
        
        # Count sections
        sections = ["Critical Issues", "Major Concerns", "Recommendations", "Security"]
        found_sections = sum(1 for section in sections if section in result)
        
        print(f"Architect: {colored(self.architect_name, 'cyan')}")
        print(f"Execution Time: {colored(f'{elapsed:.1f}s', 'green')}")
        print(f"Review Length: {colored(f'{len(result)} chars', 'blue')}")
        print(f"Sections Found: {colored(f'{found_sections}/{len(sections)}', 'yellow')}")
        
        # Performance rating
        if elapsed < 5:
            perf = colored("Excellent", "green")
        elif elapsed < 15:
            perf = colored("Good", "yellow")
        else:
            perf = colored("Slow", "red")
        print(f"Performance: {perf}")
        
        print(colored("\n✅ Test passed!", "green", attrs=['bold']))
    
    def _run_demo_mode(self):
        """Run in demo mode with mock results"""
        print(colored(f"\n🎭 Running in DEMO MODE", "yellow", attrs=['bold']))
        print(colored("=" * 60, "yellow"))
        
        # Simulate review
        print(colored("⏳ Simulating architect review...", "yellow"))
        time.sleep(2)  # Simulate processing time
        
        # Mock result
        mock_result = """
🔍 ARCHITECT'S SECURITY REVIEW
==============================

## Critical Issues 🚨
• SQL Injection vulnerability in process_user_input function
• Command injection through subprocess.run with shell=True
• Dangerous eval() usage on user input
• Hardcoded credentials in source code

## Major Concerns ⚠️
• Path traversal vulnerability in file operations
• Plaintext password comparison
• Predictable token generation using basic random

## Recommendations 💡
• Use parameterized queries to prevent SQL injection
• Avoid shell=True in subprocess calls
• Never use eval() on user input
• Store credentials in environment variables
• Implement proper input validation
• Use cryptographically secure random for tokens
"""
        
        print(colored("✅ Demo review completed", "green"))
        print(mock_result)
        
        # Run verifications
        self._verify_review_results(mock_result)
        self._display_summary(mock_result, 2.0)


if __name__ == "__main__":
    # Display test header
    print(colored("\n🎭 Statler & Waldorf Architect Test Suite", "cyan", attrs=['bold']))
    print(colored("=" * 60, "cyan"))
    
    # Show environment info
    if os.environ.get('OPENROUTER_API_KEY'):
        print(f"OpenRouter API: {colored('Configured', 'green')}")
    else:
        print(f"OpenRouter API: {colored('Not configured', 'yellow')}")
    
    ollama_base = os.environ.get('OLLAMA_API_BASE', 'http://localhost:11434')
    print(f"Ollama Base: {colored(ollama_base, 'blue')}")
    
    # Run tests
    unittest.main(verbosity=2)