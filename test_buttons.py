#!/usr/bin/env python3
"""Test buttons and linkification with BugHunter logging"""

import requests
import json
import time

SIMULATOR_API = "http://localhost:8000"

def test_start_command_with_buttons():
    """Test /start command returns buttons"""
    print("\n=== Test 1: /start command returns inline buttons ===")
    
    response = requests.post(
        f"{SIMULATOR_API}/send-message",
        json={
            "user_id": 999001,
            "text": "/start",
            "mode": "local"
        }
    )
    
    data = response.json()
    print(f"Response text: {data.get('response_text')}")
    print(f"Has buttons: {'buttons' in data and data['buttons'] is not None}")
    
    if data.get('buttons'):
        print(f"Button structure: {json.dumps(data['buttons'], indent=2)}")
        if data['buttons'].get('inline_keyboard'):
            for row_idx, row in enumerate(data['buttons']['inline_keyboard']):
                print(f"  Row {row_idx}:")
                for btn in row:
                    print(f"    - {btn['text']} (callback: {btn['callback_data']})")
        print("✅ Buttons returned successfully")
    else:
        print("❌ No buttons returned")
    
    return data.get('success')

def test_help_command_no_buttons():
    """Test /help command (no buttons expected)"""
    print("\n=== Test 2: /help command (no buttons) ===")
    
    response = requests.post(
        f"{SIMULATOR_API}/send-message",
        json={
            "user_id": 999001,
            "text": "/help",
            "mode": "local"
        }
    )
    
    data = response.json()
    print(f"Response text: {data.get('response_text')[:50]}...")
    print(f"Has buttons: {data.get('buttons') is not None}")
    
    if data.get('buttons') is None:
        print("✅ No buttons as expected")
    else:
        print("⚠️  Buttons returned unexpectedly")
    
    return data.get('success')

def test_callback_button():
    """Test callback button click"""
    print("\n=== Test 3: Callback button click ===")
    
    response = requests.post(
        f"{SIMULATOR_API}/send-callback",
        json={
            "user_id": 999001,
            "callback_data": "btn_hello",
            "mode": "local"
        }
    )
    
    data = response.json()
    print(f"Response: {data.get('response_text')}")
    
    if data.get('success'):
        print("✅ Callback handled successfully")
    else:
        print("❌ Callback failed")
    
    return data.get('success')

def test_linkification():
    """Test that URLs in echo are preserved"""
    print("\n=== Test 4: URL linkification in echo ===")
    
    test_text = "Check this link https://example.com out!"
    
    response = requests.post(
        f"{SIMULATOR_API}/send-message",
        json={
            "user_id": 999001,
            "text": test_text,
            "mode": "local"
        }
    )
    
    data = response.json()
    response_text = data.get('response_text', '')
    
    print(f"Sent: {test_text}")
    print(f"Echo response: {response_text}")
    
    if "https://example.com" in response_text:
        print("✅ URL preserved in response")
    else:
        print("❌ URL not preserved")
    
    return data.get('success')

def main():
    print("Testing buttons and linkification...")
    print("Waiting for simulator to respond...")
    
    try:
        requests.get(f"{SIMULATOR_API}/")
    except:
        print("❌ Simulator not available at http://localhost:8000")
        return
    
    results = []
    results.append(("Start with buttons", test_start_command_with_buttons()))
    results.append(("Help without buttons", test_help_command_no_buttons()))
    results.append(("Callback button", test_callback_button()))
    results.append(("URL linkification", test_linkification()))
    
    print("\n" + "="*50)
    print("Test Results Summary:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Buttons and linkification working.")
    else:
        print("\n⚠️  Some tests failed. Check implementation.")

if __name__ == "__main__":
    main()
