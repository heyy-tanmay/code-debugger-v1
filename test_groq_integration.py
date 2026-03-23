#!/usr/bin/env python3
"""
═════════════════════════════════════════════════════════════════════════════
                    GROQ LLM INTEGRATION TEST SCRIPT
                   Test all Groq endpoints before deployment
═════════════════════════════════════════════════════════════════════════════

This script tests:
1. Groq API connection
2. Bug explanation endpoint
3. Code fix suggestion endpoint
4. Security analysis endpoint
5. Integration with CodeBERT predictions

Usage:
    python test_groq_integration.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000"

# Test data - various bug types
TEST_CASES = {
    "buffer_overflow": {
        "buggy_code": """#include <stdio.h>
int main() {
    int arr[5];
    for(int i = 0; i < 100; i++) {
        arr[i] = i;
    }
    return 0;
}""",
        "bug_type": "Buffer Overflow"
    },
    
    "null_pointer": {
        "buggy_code": """public class Test {
    public void process(String str) {
        int len = str.length();
    }
}""",
        "bug_type": "Null Pointer Exception"
    },
    
    "use_after_free": {
        "buggy_code": """#include <stdlib.h>
int main() {
    int *ptr = (int*)malloc(sizeof(int));
    free(ptr);
    ptr[0] = 42;
    return 0;
}""",
        "bug_type": "Use After Free"
    }
}

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def print_result(title: str, content: str):
    """Print formatted result"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}{title}:{Colors.ENDC}")
    print(Colors.CYAN + content[:500] + ("..." if len(content) > 500 else "") + Colors.ENDC)

def test_groq_connection():
    """Test if Groq is properly integrated"""
    print_header("Testing Groq LLM Connection")
    
    try:
        response = requests.get(f"{API_URL}/metrics")
        metrics = response.json()
        
        llm_enabled = metrics.get("llm_enabled", False)
        llm_model = metrics.get("llm_model", "Unknown")
        
        if llm_enabled:
            print_success(f"Groq LLM is enabled: {llm_model}")
            return True
        else:
            print_error("Groq LLM is disabled. Check GROQ_API_KEY in .env")
            return False
    
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Make sure API server is running: python api_server.py")
        return False

def test_bug_explanation():
    """Test bug explanation endpoint"""
    print_header("Testing Bug Explanation Endpoint")
    
    test_case = TEST_CASES["buffer_overflow"]
    
    try:
        print_info(f"Requesting explanation for: {test_case['bug_type']}")
        
        response = requests.post(
            f"{API_URL}/explain_bug",
            json={
                "bug_type": test_case["bug_type"],
                "code_snippet": test_case["buggy_code"],
                "context": "Test explanation request"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Explanation generated successfully")
            print_result("Bug Type", test_case["bug_type"])
            print_result("Explanation", data["explanation"])
            return True
        else:
            print_error(f"API error: {response.status_code}")
            print_result("Response", response.text)
            return False
    
    except requests.Timeout:
        print_error("Request timeout (>30s). Groq might be slow or offline.")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_code_fix():
    """Test code fix suggestion endpoint"""
    print_header("Testing Code Fix Suggestion Endpoint")
    
    test_case = TEST_CASES["null_pointer"]
    
    try:
        print_info(f"Requesting fix for: {test_case['bug_type']}")
        
        response = requests.post(
            f"{API_URL}/suggest_fix",
            json={
                "bug_type": test_case["bug_type"],
                "code_snippet": test_case["buggy_code"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Fix suggestion generated successfully")
            print_result("Bug Type", test_case["bug_type"])
            print_result("Suggested Fix", data["suggested_fix"])
            return True
        else:
            print_error(f"API error: {response.status_code}")
            return False
    
    except requests.Timeout:
        print_error("Request timeout. Groq is slow.")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_security_analysis():
    """Test security analysis endpoint"""
    print_header("Testing Security Analysis Endpoint")
    
    test_case = TEST_CASES["use_after_free"]
    
    try:
        print_info("Requesting security analysis...")
        
        response = requests.post(
            f"{API_URL}/security_analysis",
            json={
                "code_snippet": test_case["buggy_code"],
                "language": "C",
                "filename": "test.c"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Security analysis completed")
            print_result("Analysis Result", data["security_analysis"])
            return True
        else:
            print_error(f"API error: {response.status_code}")
            return False
    
    except requests.Timeout:
        print_error("Request timeout.")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_predict_bug():
    """Test CodeBERT prediction endpoint"""
    print_header("Testing CodeBERT Prediction (Existing)")
    
    test_code = TEST_CASES["buffer_overflow"]["buggy_code"]
    
    try:
        response = requests.post(
            f"{API_URL}/predict_bug",
            json={
                "code_snippet": test_code,
                "language": "C",
                "filename": "test.c"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Bug prediction successful")
            print_result("Bug Detected", str(data["bug_detected"]))
            print_result("Confidence", f"{data['confidence_score']*100:.1f}%")
            print_result("Issue Type", data["likely_issue"])
            return True
        else:
            print_error(f"API error: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print_header("GROQ LLM INTEGRATION TEST SUITE")
    
    results = {}
    
    # Test 1: Connection
    print_info("Test 1/5: Checking Groq connection...")
    results["connection"] = test_groq_connection()
    time.sleep(1)
    
    if not results["connection"]:
        print_error("\nGroq is not configured properly. Skipping remaining LLM tests.")
        print_info("Check your .env file for GROQ_API_KEY")
        return results
    
    # Test 2: CodeBERT prediction
    print_info("Test 2/5: Testing CodeBERT prediction...")
    results["predict"] = test_predict_bug()
    time.sleep(2)
    
    # Test 3: Explanation
    print_info("Test 3/5: Testing bug explanation...")
    results["explain"] = test_bug_explanation()
    time.sleep(2)
    
    # Test 4: Fix suggestion
    print_info("Test 4/5: Testing code fix suggestion...")
    results["fix"] = test_code_fix()
    time.sleep(2)
    
    # Test 5: Security analysis
    print_info("Test 5/5: Testing security analysis...")
    results["security"] = test_security_analysis()
    
    return results

def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    tests = {
        "connection": "Groq Connection",
        "predict": "CodeBERT Prediction",
        "explain": "Bug Explanation",
        "fix": "Code Fix Suggestion",
        "security": "Security Analysis"
    }
    
    passed = 0
    failed = 0
    
    for key, name in tests.items():
        if key in results:
            if results[key]:
                print_success(f"{name}")
                passed += 1
            else:
                print_error(f"{name}")
                failed += 1
    
    print(f"\n{Colors.BOLD}Results: {passed} passed, {failed} failed{Colors.ENDC}\n")
    
    if failed == 0:
        print_success("All tests passed! Your Groq integration is working! 🎉")
    else:
        print_error(f"{failed} test(s) failed. Check the logs above.")

if __name__ == "__main__":
    try:
        results = run_all_tests()
        print_summary(results)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user.{Colors.ENDC}")
    except Exception as e:
        print_error(f"Fatal error: {e}")
