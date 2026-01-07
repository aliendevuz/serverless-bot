"""
Environment layer - manages Telegram API integration
"""

import os
import requests
from application import handle_message


class TelegramEnvironment:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def process_message(self, message_data):
        """
        Process message through application layer and prepare response
        
        Args:
            message_data: Dictionary containing message info
            
        Returns:
            Dictionary with response and chat_id
        """
        # Handle the message through application layer
        response = handle_message(message_data)
        
        return {
            "chat_id": message_data.get("chat_id"),
            "text": response.get("text")
        }
    
    def send_message(self, response_data):
        """
        Send message to Telegram via API
        
        Args:
            response_data: Dictionary with chat_id and text
            
        Returns:
            Boolean indicating success
        """
        try:
            payload = {
                "chat_id": response_data.get("chat_id"),
                "text": response_data.get("text")
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
