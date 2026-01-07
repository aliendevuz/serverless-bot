"""
Application layer - handles the actual business logic of processing messages
"""


def handle_message(message_data):
    """
    Process incoming message and generate response
    
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
