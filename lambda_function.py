import json
import os
import requests


# ============= APPLICATION LAYER =============
def handle_message(message_data):
    """
    Application layer - handles the actual business logic of processing messages
    
    Args:
        message_data: Dictionary containing message information
        
    Returns:
        Dictionary with the response text
    """
    text = message_data.get("text", "")
    
    # Simple echo response with emoji
    response_text = f"Siz yuborganingiz: {text} ✅"
    
    return {
        "text": response_text
    }


# ============= ENVIRONMENT LAYER =============
class TelegramEnvironment:
    def __init__(self):
        self.bot_token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
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


# ============= ADAPTER LAYER =============
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


# ============= LAMBDA HANDLER =============
def lambda_handler(event, context):
    """
    AWS Lambda handler for Telegram webhook
    
    Flow:
    1. Receives webhook event from Telegram
    2. Passes to adapter
    3. Adapter -> Environment -> Application (processing)
    4. Application -> Environment -> Adapter (response)
    5. Adapter sends response to Telegram
    6. Returns success status to Lambda
    """
    try:
        # Parse incoming webhook event
        body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        
        # Initialize adapter and process update
        adapter = TelegramAdapter()
        result = adapter.process_update(body)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "result": "ok",
                "message": "Lambda executed successfully",
                "details": result
            }),
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "result": "error",
                "message": str(e)
            }),
        }
