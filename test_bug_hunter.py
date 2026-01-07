#!/usr/bin/env python3
"""Test BugHunter logging system"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import BugHunter

def test_bug_hunter():
    """Test bug hunter with dummy token"""
    print("Testing BugHunter logger...")
    print()
    
    # Test 1: Without environment variables (should be disabled)
    print("Test 1: Without BUG_HUNTER_BOT_TOKEN")
    bug_hunter = BugHunter()
    print(f"  BugHunter enabled: {bug_hunter.enabled}")
    print(f"  Token: {bug_hunter.token}")
    print(f"  Chat ID: {bug_hunter.chat_id}")
    
    # Test 2: With dummy token set
    print()
    print("Test 2: Setting dummy environment variables")
    os.environ["BUG_HUNTER_BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    os.environ["BUG_HUNTER_CHAT_ID"] = "-987654321"
    
    bug_hunter2 = BugHunter()
    print(f"  BugHunter enabled: {bug_hunter2.enabled}")
    print(f"  Token set: {bool(bug_hunter2.token)}")
    print(f"  Chat ID set: {bool(bug_hunter2.chat_id)}")
    
    # Test 3: Try logging error (will fail with dummy token but shows structure)
    print()
    print("Test 3: Attempting to log error with dummy token")
    result = bug_hunter2.log_error(
        error_type="TEST_ERROR",
        error_msg="This is a test error message",
        stack_trace="Line 1 of stack\nLine 2 of stack",
        context_data={"test_key": "test_value"}
    )
    print(f"  Log result: {result}")
    print(f"  (Result should be False with invalid token)")
    
    print()
    print("✅ BugHunter structure test completed")
    print()
    print("IMPORTANT: Set these in AWS Lambda environment variables:")
    print("  BUG_HUNTER_BOT_TOKEN=<your_bot_token>")
    print("  BUG_HUNTER_CHAT_ID=<your_chat_id>")

if __name__ == "__main__":
    test_bug_hunter()
