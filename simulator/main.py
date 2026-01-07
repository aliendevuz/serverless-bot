"""
Telegram Bot Simulator - FastAPI server
Simulates Telegram webhook and communicates with bot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import Optional, List
import requests
from datetime import datetime

app = FastAPI(title="Telegram Bot Simulator")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LAMBDA_WEBHOOK_URL = os.environ.get(
    "LAMBDA_WEBHOOK_URL",
    "https://vwn78888d8.execute-api.eu-central-1.amazonaws.com/main"
)
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "mock_data.json")

# Load mock data
def load_mock_data():
    with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

MOCK_DATA = load_mock_data()


# ============= MODELS =============
class MessageRequest(BaseModel):
    """Frontend sends message request"""
    user_id: int
    text: str
    chat_id: Optional[int] = None


class BotResponse(BaseModel):
    """Bot response with message and optional inline buttons"""
    text: str
    buttons: Optional[List[dict]] = None


class ChatMessage(BaseModel):
    """Message in chat history"""
    sender: str  # "user" or "bot"
    text: str
    timestamp: str


# ============= HELPERS =============
def get_user_by_id(user_id: int):
    """Get user from mock data"""
    for user in MOCK_DATA["users"]:
        if user["id"] == user_id:
            return user
    return None


def get_chat_by_id(chat_id: int):
    """Get chat from mock data"""
    for chat in MOCK_DATA["chats"]:
        if chat["id"] == chat_id:
            return chat
    return None


def create_telegram_update(user_id: int, chat_id: int, message_text: str):
    """Create Telegram-like update JSON"""
    user = get_user_by_id(user_id)
    chat = get_chat_by_id(chat_id)
    
    if not user or not chat:
        raise ValueError(f"User or chat not found")
    
    return {
        "update_id": int(datetime.now().timestamp() * 1000),
        "message": {
            "message_id": int(datetime.now().timestamp() * 1000),
            "date": int(datetime.now().timestamp()),
            "chat": {
                "id": chat["id"],
                "type": chat["type"],
                "first_name": chat.get("first_name"),
                "username": chat.get("username")
            },
            "from": {
                "id": user["id"],
                "is_bot": user["is_bot"],
                "first_name": user["first_name"],
                "last_name": user.get("last_name"),
                "username": user.get("username"),
                "language_code": user.get("language_code")
            },
            "text": message_text
        }
    }


# ============= ENDPOINTS =============
@app.get("/", tags=["Health"])
async def health():
    """Health check"""
    return {
        "status": "ok",
        "simulator": "running",
        "lambda_url": LAMBDA_WEBHOOK_URL
    }


@app.get("/users", tags=["Mock Data"])
async def get_users():
    """Get all mock users"""
    return {"users": MOCK_DATA["users"]}


@app.get("/users/{user_id}", tags=["Mock Data"])
async def get_user(user_id: int):
    """Get specific mock user"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/send-message", tags=["Chat"])
async def send_message(request: MessageRequest):
    """
    Frontend sends message to bot
    
    1. Create Telegram-like update
    2. Send to Lambda webhook
    3. Return bot response
    """
    try:
        # Use provided chat_id or default to user_id
        chat_id = request.chat_id or request.user_id
        
        # Verify user exists
        user = get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create Telegram update
        update = create_telegram_update(request.user_id, chat_id, request.text)
        
        # Send to Lambda webhook
        response = requests.post(
            LAMBDA_WEBHOOK_URL,
            json=update,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "X-Simulator": "true"  # Mark as simulator request
            }
        )
        
        # Parse Lambda response
        if response.status_code == 200:
            lambda_response = response.json()
            
            # Extract bot response from lambda
            details = lambda_response.get("details", {})
            
            return {
                "success": details.get("success", False),
                "message": details.get("message", ""),
                "bot_response": {
                    "text": "Bot xabar yubordi (test mode)",
                    "buttons": []
                },
                "raw_response": lambda_response
            }
        else:
            return {
                "success": False,
                "message": f"Lambda error: {response.status_code}",
                "raw_response": response.text
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhook-test", tags=["Debug"])
async def webhook_test():
    """Test webhook with sample message"""
    try:
        user = MOCK_DATA["users"][0]
        update = create_telegram_update(user["id"], user["id"], "Test xabar")
        
        response = requests.post(
            LAMBDA_WEBHOOK_URL,
            json=update,
            timeout=10,
            headers={"X-Simulator": "true"}
        )
        
        return {
            "status": "ok",
            "update_sent": update,
            "lambda_response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
