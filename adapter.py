"""
Adapter layer - processes Telegram webhook updates and coordinates communication
"""

from environment import TelegramEnvironment


class TelegramAdapter:
    def __init__(self):
        self.telegram_env = TelegramEnvironment()
    
    def process_update(self, update):
        """
        Process incoming Telegram update
        
        Args:
            update: Telegram update object from webhook
            
        Returns:
            Dictionary with success status
        """
        try:
            # Extract message from update
            message = update.get("message", {})
            
            if not message:
                return {"success": False, "error": "No message in update"}
            
            # Prepare message data for environment
            message_data = {
                "chat_id": message.get("chat", {}).get("id"),
                "text": message.get("text", ""),
                "message_id": message.get("message_id"),
                "user_id": message.get("from", {}).get("id")
            }
            
            # Pass to environment for processing
            response_data = self.telegram_env.process_message(message_data)
            
            # Send response back through environment
            success = self.telegram_env.send_message(response_data)
            
            return {
                "success": success,
                "message": "Message processed and sent" if success else "Failed to send message"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
