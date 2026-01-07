#!/usr/bin/env python
"""Test simulator endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_message(user_id: int, text: str):
    """Test /send-message endpoint"""
    print(f"\n{'='*50}")
    print(f"TEST: Send Message - '{text}'")
    print(f"{'='*50}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/send-message",
            json={"user_id": user_id, "text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['success']}")
            print(f"📝 Response: {data['response_text']}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Details: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is simulator running?")
        print("   Run: python simulator/main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_callback(user_id: int, callback_data: str):
    """Test /send-callback endpoint"""
    print(f"\n{'='*50}")
    print(f"TEST: Send Callback - '{callback_data}'")
    print(f"{'='*50}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/send-callback",
            json={"user_id": user_id, "callback_data": callback_data},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['success']}")
            print(f"📝 Response: {data['response_text']}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Details: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is simulator running?")
        print("   Run: python simulator/main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_health():
    """Test health check endpoint"""
    print(f"\n{'='*50}")
    print(f"TEST: Health Check")
    print(f"{'='*50}")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"   Simulator: {data['simulator']}")
            print(f"   Lambda URL: {data['lambda_url']}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is simulator running?")
        print("   Run: python simulator/main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("\n🤖 SIMULATOR ENDPOINT TESTS\n")
    
    # Test health
    test_health()
    
    # Test messages
    test_message(12345, "/start")
    test_message(12345, "/help")
    test_message(12345, "/info")
    test_message(12345, "/echo Salom, dunyo!")
    test_message(12345, "Oddiy xabar")
    
    # Test callbacks
    test_callback(12345, "btn_hello")
    test_callback(12345, "btn_help")
    test_callback(12345, "btn_info")
    
    print(f"\n{'='*50}")
    print("✅ TEST SEQUENCE COMPLETED!")
    print(f"{'='*50}\n")
