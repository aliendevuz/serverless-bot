"""
Telegram Bot Simulator - FastAPI server
Simulates Telegram webhook and communicates with bot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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


# ============= MODELS =============
class MessageRequest(BaseModel):
    """Frontend sends message request"""
    user_id: int
    text: str
    chat_id: Optional[int] = None


class CallbackRequest(BaseModel):
    """Frontend sends callback request"""
    user_id: int
    callback_data: str


def create_telegram_update(user_id: int, message_text: str):
    """
    Create Telegram-like update JSON for webhook
    Frontend provides user info, we just create the update structure
    """
    current_timestamp = int(datetime.now().timestamp())
    message_id = int(datetime.now().timestamp() * 1000)
    
    return {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "date": current_timestamp,
            "chat": {
                "id": user_id,
                "type": "private"
            },
            "from": {
                "id": user_id,
                "is_bot": False
            },
            "text": message_text
        }
    }


def create_callback_update(user_id: int, callback_data: str):
    """
    Create Telegram-like callback_query update
    Simulates a button click on inline keyboard
    """
    current_timestamp = int(datetime.now().timestamp())
    callback_id = f"callback_{int(datetime.now().timestamp() * 1000)}"
    
    return {
        "update_id": int(datetime.now().timestamp() * 1000),
        "callback_query": {
            "id": callback_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "User"
            },
            "data": callback_data,
            "message": {
                "message_id": 1,
                "date": current_timestamp,
                "chat": {
                    "id": user_id,
                    "type": "private"
                },
                "text": "Menu"
            }
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


@app.post("/send-message", tags=["Chat"])
async def send_message(request: MessageRequest):
    """
    Frontend sends message to bot via Simulator
    
    Flow:
    1. Create Telegram-like update from user message
    2. Send to REAL Lambda webhook (as if it's Telegram)
    3. Lambda processes it (doesn't know it's simulator)
    4. Lambda returns response (containing bot reply)
    5. Extract bot response and return to frontend
    """
    try:
        # Create REAL Telegram-like update
        update = create_telegram_update(request.user_id, request.text)
        
        print(f"[SIMULATOR] Sending update to webhook: {LAMBDA_WEBHOOK_URL}")
        print(f"[SIMULATOR] User ID: {request.user_id}, Message: {request.text}")
        
        # Send to Lambda webhook as if it's a real Telegram webhook
        response = requests.post(
            LAMBDA_WEBHOOK_URL,
            json=update,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "X-Simulator": "true"  # Mark as simulator for logging
            }
        )
        
        print(f"[SIMULATOR] Lambda response status: {response.status_code}")
        
        # Parse Lambda response
        if response.status_code == 200:
            lambda_response = response.json()
            
            # Extract bot response from lambda details
            details = lambda_response.get("details", {})
            response_text = details.get("response_text", "Javob topilmadi")
            
            return {
                "success": details.get("success", False),
                "message": details.get("message", ""),
                "response_text": response_text,
                "raw_response": lambda_response
            }
        else:
            return {
                "success": False,
                "message": f"Lambda webhook error: {response.status_code}",
                "response_text": f"❌ Webhook xatosi: {response.status_code}",
                "raw_response": response.text
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Webhook timeout",
            "response_text": "❌ Webhook javob bermadi (timeout)",
            "error": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        print(f"[SIMULATOR] Connection error: {str(e)}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "response_text": f"❌ Ulanish xatosi: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        print(f"[SIMULATOR] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-callback", tags=["Chat"])
async def send_callback(request: CallbackRequest):
    """
    Frontend sends callback (button click) to bot via Simulator
    
    Flow:
    1. Create Telegram-like callback_query update
    2. Send to Lambda webhook (as if it's a real Telegram callback)
    3. Lambda processes it
    4. Lambda returns response
    5. Return bot's reply to frontend
    """
    try:
        # Create REAL Telegram-like callback update
        update = create_callback_update(request.user_id, request.callback_data)
        
        print(f"[SIMULATOR] Sending callback to webhook: {LAMBDA_WEBHOOK_URL}")
        print(f"[SIMULATOR] User ID: {request.user_id}, Callback: {request.callback_data}")
        
        # Send to Lambda webhook
        response = requests.post(
            LAMBDA_WEBHOOK_URL,
            json=update,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "X-Simulator": "true"
            }
        )
        
        print(f"[SIMULATOR] Lambda response status: {response.status_code}")
        
        # Parse Lambda response
        if response.status_code == 200:
            lambda_response = response.json()
            details = lambda_response.get("details", {})
            response_text = details.get("response_text", "Javob topilmadi")
            
            return {
                "success": details.get("success", False),
                "message": details.get("message", ""),
                "response_text": response_text,
                "raw_response": lambda_response
            }
        else:
            return {
                "success": False,
                "message": f"Lambda webhook error: {response.status_code}",
                "response_text": f"❌ Webhook xatosi: {response.status_code}",
                "raw_response": response.text
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Webhook timeout",
            "response_text": "❌ Webhook javob bermadi (timeout)",
            "error": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        print(f"[SIMULATOR] Connection error: {str(e)}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "response_text": f"❌ Ulanish xatosi: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        print(f"[SIMULATOR] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
