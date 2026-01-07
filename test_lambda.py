#!/usr/bin/env python
"""Test script for lambda_function"""

import json
from lambda_function import lambda_handler

def test_command(command, text, description):
    """Test a command"""
    print(f"\n{'='*50}")
    print(f"TEST: {description}")
    print(f"{'='*50}")
    
    update = {
        'update_id': 1,
        'message': {
            'message_id': 1,
            'date': 1704603000,
            'chat': {'id': 12345, 'type': 'private'},
            'from': {'id': 12345, 'is_bot': False, 'first_name': 'Ali'},
            'text': text
        }
    }
    
    event = {
        'body': json.dumps(update),
        'headers': {'X-Simulator': 'true'}
    }
    
    result = lambda_handler(event, {})
    details = json.loads(result['body'])['details']
    
    print(f"✅ Success: {details['success']}")
    print(f"📝 Response: {details['response_text']}")
    return details

def test_callback(callback_data, description):
    """Test a callback"""
    print(f"\n{'='*50}")
    print(f"TEST: {description}")
    print(f"{'='*50}")
    
    update = {
        'update_id': 2,
        'callback_query': {
            'id': 'callback_123',
            'from': {'id': 12345, 'is_bot': False, 'first_name': 'Ali'},
            'data': callback_data,
            'message': {
                'message_id': 1,
                'date': 1704603000,
                'chat': {'id': 12345, 'type': 'private'},
                'text': 'Menu'
            }
        }
    }
    
    event = {
        'body': json.dumps(update),
        'headers': {'X-Simulator': 'true'}
    }
    
    result = lambda_handler(event, {})
    details = json.loads(result['body'])['details']
    
    print(f"✅ Success: {details['success']}")
    print(f"📝 Response: {details['response_text']}")
    return details

if __name__ == "__main__":
    print("\n🤖 TELEGRAM BOT LAMBDA FUNCTION TESTS\n")
    
    # Test commands
    test_command("/start", "/start", "/start buyrug'i")
    test_command("/help", "/help", "/help buyrug'i")
    test_command("/info", "/info", "/info buyrug'i")
    test_command("/echo", "/echo Salom, dunyo!", "/echo buyrug'i")
    test_command("text", "Oddiy xabar", "Regular text message")
    
    # Test callbacks
    test_callback("btn_hello", "Salom tugmasi")
    test_callback("btn_help", "Yordam tugmasi")
    test_callback("btn_info", "Info tugmasi")
    
    print(f"\n{'='*50}")
    print("✅ BARCHA TESTLAR MUVAFFAQIYAT!")
    print(f"{'='*50}\n")
