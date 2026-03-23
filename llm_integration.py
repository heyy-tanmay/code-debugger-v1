"""
═════════════════════════════════════════════════════════════════════════════
                       LLM INTEGRATION MODULE
                   (Groq Llama-Based Explanations)
═════════════════════════════════════════════════════════════════════════════

This module integrates Groq's Llama LLM to provide:
1. Enhanced bug explanations and recommendations
2. Code fix suggestions
3. Security analysis
4. Performance optimization tips

Libraries Used:
- groq: Groq API client for LLM access
- os: Environment variable loading
═════════════════════════════════════════════════════════════════════════════
"""

import os
from groq import Groq
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GROQ CLIENT INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

class GroqLLMManager:
    """
    Singleton manager for Groq LLM API interactions.
    
    Provides methods for:
    - Bug explanation generation
    - Code fix suggestions
    - Security analysis
    """
    
    _instance = None
    client = None
    model = None
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super(GroqLLMManager, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize Groq client"""
        try:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning("⚠️  GROQ_API_KEY not found in .env file")
                logger.warning("LLM features will be disabled")
                self.client = None
                return
            
            self.client = Groq(api_key=api_key)
            self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
            logger.info(f"✓ Groq LLM initialized")
            logger.info(f"  - Model: {self.model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            self.client = None
    
    def explain_bug(self, bug_type: str, code_snippet: str, context: str = "") -> str:
        """
        Generate a detailed explanation of a detected bug.
        
        Args:
            bug_type: Type of bug (e.g., "Buffer Overflow")
            code_snippet: The code that contains the bug
            context: Additional context about the bug
        
        Returns:
            Detailed explanation from Llama
        """
        
        if not self.client:
            return "LLM service not available. Check GROQ_API_KEY in .env"
        
        try:
            prompt = f"""
            You are a security expert analyzing C and Java code for bugs.
            
            Bug Detected: {bug_type}
            
            Code:
            ```
            {code_snippet}
            ```
            
            Context: {context if context else "N/A"}
            
            Please provide:
            1. A clear explanation of what this bug is
            2. Why it's dangerous
            3. How to fix it
            4. Best practices to prevent it
            
            Keep your response concise and technical (max 200 words).
            """
            
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,        # Balanced creativity
                max_completion_tokens=500,
                top_p=1,
                stop=None
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return f"Error: Could not generate explanation. {str(e)}"
    
    def suggest_fix(self, bug_type: str, code_snippet: str) -> str:
        """
        Generate a suggested code fix for the detected bug.
        
        Args:
            bug_type: Type of bug
            code_snippet: Buggy code
        
        Returns:
            Suggested fixed code
        """
        
        if not self.client:
            return "LLM service not available."
        
        try:
            prompt = f"""
            You are an expert C and Java developer.
            
            The following code has a {bug_type} bug:
            
            ```
            {code_snippet[:500]}  # Limit to 500 chars
            ```
            
            Provide a corrected version of this code that fixes the bug.
            Only return the corrected code, no explanation.
            Wrap code in triple backticks.
            """
            
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,        # Lower = more consistent
                max_completion_tokens=400,
                top_p=1,
                stop=None
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error suggesting fix: {e}")
            return f"Error generating fix suggestion: {str(e)}"
    
    def analyze_security(self, code_snippet: str) -> str:
        """
        Perform security analysis on code.
        
        Args:
            code_snippet: Code to analyze
        
        Returns:
            Security analysis report
        """
        
        if not self.client:
            return "LLM service not available."
        
        try:
            prompt = f"""
            You are a security auditor. Analyze this code for security vulnerabilities:
            
            ```
            {code_snippet[:500]}
            ```
            
            Identify:
            1. Security vulnerabilities
            2. Memory safety issues
            3. Input validation problems
            4. Risk level (Low/Medium/High/Critical)
            
            Keep response to max 150 words.
            """
            
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_completion_tokens=300,
                top_p=1,
                stop=None
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error analyzing security: {e}")
            return f"Error: {str(e)}"
    
    def optimize_performance(self, code_snippet: str) -> str:
        """
        Suggest performance optimizations.
        
        Args:
            code_snippet: Code to optimize
        
        Returns:
            Performance optimization suggestions
        """
        
        if not self.client:
            return "LLM service not available."
        
        try:
            prompt = f"""
            You are a performance optimization expert.
            
            Suggest optimizations for this code:
            ```
            {code_snippet[:500]}
            ```
            
            Provide:
            1. Performance bottlenecks
            2. Optimization suggestions
            3. Estimated improvement
            
            Keep to max 150 words.
            """
            
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_completion_tokens=300,
                top_p=1,
                stop=None
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error optimizing performance: {e}")
            return f"Error: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_bug_explanation(bug_type: str, code_snippet: str) -> str:
    """
    Convenience function to get bug explanation.
    
    Args:
        bug_type: Type of bug detected
        code_snippet: Code containing the bug
    
    Returns:
        Explanation from Groq Llama
    """
    manager = GroqLLMManager()
    return manager.explain_bug(bug_type, code_snippet)


def get_code_fix(bug_type: str, code_snippet: str) -> str:
    """
    Convenience function to get code fix suggestion.
    
    Args:
        bug_type: Type of bug
        code_snippet: Buggy code
    
    Returns:
        Fixed code suggestion
    """
    manager = GroqLLMManager()
    return manager.suggest_fix(bug_type, code_snippet)


def get_security_analysis(code_snippet: str) -> str:
    """
    Convenience function for security analysis.
    
    Args:
        code_snippet: Code to analyze
    
    Returns:
        Security analysis report
    """
    manager = GroqLLMManager()
    return manager.analyze_security(code_snippet)


# ─────────────────────────────────────────────────────────────────────────────
# TESTING
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING GROQ LLM INTEGRATION")
    print("="*80 + "\n")
    
    # Test code with buffer overflow
    test_code = """
    #include <stdio.h>
    int main() {
        int arr[5];
        for(int i = 0; i < 100; i++) {
            arr[i] = i;  // Buffer overflow!
        }
        return 0;
    }
    """
    
    manager = GroqLLMManager()
    
    if manager.client:
        print("✓ Testing bug explanation:")
        explanation = manager.explain_bug("Buffer Overflow", test_code)
        print(explanation)
        
        print("\n" + "="*80 + "\n")
        
        print("✓ Testing code fix suggestion:")
        fix = manager.suggest_fix("Buffer Overflow", test_code)
        print(fix)
    else:
        print("⚠️  Groq client not initialized. Check API key in .env")
