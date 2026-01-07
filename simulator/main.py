"""
Telegram Bot Simulator - FastAPI server
Simulates Telegram webhook and communicates with bot

Modes:
- local: Call lambda_function.lambda_handler directly (for local testing)
- aws: Call real AWS Lambda webhook (production)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Optional, Literal
import requests
from datetime import datetime
import json
import sys

# Add parent directory to path to import lambda_function
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from lambda_function import lambda_handler as local_lambda_handler
    LAMBDA_AVAILABLE = True
except ImportError:
    LAMBDA_AVAILABLE = False
    print("[WARNING] lambda_function not found - local mode disabled")

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
    mode: Literal["local", "aws"] = "local"  # Which Lambda to call
    chat_id: Optional[int] = None


class CallbackRequest(BaseModel):
    """Frontend sends callback request"""
    user_id: int
    callback_data: str
    mode: Literal["local", "aws"] = "local"  # Which Lambda to call


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


def call_local_lambda(update_dict):
    """Call lambda_function.lambda_handler locally (mock serverless environment)"""
    try:
        if not LAMBDA_AVAILABLE:
            return {
                "success": False,
                "message": "Local lambda not available",
                "response_text": "❌ Local lambda mode ishlamaydi",
                "buttons": None,
                "error": "lambda_function import failed"
            }
        
        print(f"[LOCAL LAMBDA] Calling lambda_handler with update")
        
        # Create event as AWS Lambda would
        event = {
            "body": json.dumps(update_dict),
            "headers": {"X-Simulator": "true"}
        }
        
        # Call lambda_handler directly (simulates AWS Lambda invocation)
        result = local_lambda_handler(event, context=None)
        
        print(f"[LOCAL LAMBDA] Response status: {result.get('statusCode')}")
        
        # Parse response
        if result.get("statusCode") == 200:
            body = json.loads(result.get("body", "{}"))
            details = body.get("details", {})
            
            return {
                "success": details.get("success", False),
                "message": details.get("message", ""),
                "response_text": details.get("response_text", "Javob topilmadi"),
                "buttons": details.get("buttons", None),
                "raw_response": body,
                "mode": "local"
            }
        else:
            return {
                "success": False,
                "message": f"Lambda error: {result.get('statusCode')}",
                "response_text": f"❌ Lambda xatosi: {result.get('statusCode')}",
                "buttons": None,
                "raw_response": result,
                "mode": "local"
            }
    
    except Exception as e:
        print(f"[LOCAL LAMBDA ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "response_text": f"❌ Local lambda xatosi: {str(e)}",
            "buttons": None,
            "error": str(e),
            "mode": "local"
        }


def call_aws_lambda(update_dict):
    """Call real AWS Lambda webhook (production mode)"""
    try:
        print(f"[AWS LAMBDA] Sending update to webhook: {LAMBDA_WEBHOOK_URL}")
        
        # Send to Lambda webhook as if it's a real Telegram webhook
        response = requests.post(
            LAMBDA_WEBHOOK_URL,
            json=update_dict,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "X-Simulator": "true"
            }
        )
        
        print(f"[AWS LAMBDA] Lambda response status: {response.status_code}")
        
        # Parse Lambda response
        if response.status_code == 200:
            lambda_response = response.json()
            details = lambda_response.get("details", {})
            
            return {
                "success": details.get("success", False),
                "message": details.get("message", ""),
                "response_text": details.get("response_text", "Javob topilmadi"),
                "buttons": details.get("buttons", None),
                "raw_response": lambda_response,
                "mode": "aws"
            }
        else:
            return {
                "success": False,
                "message": f"Lambda webhook error: {response.status_code}",
                "response_text": f"❌ Webhook xatosi: {response.status_code}",
                "buttons": None,
                "raw_response": response.text,
                "mode": "aws"
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Webhook timeout",
            "response_text": "❌ Webhook javob bermadi (timeout)",
            "buttons": None,
            "error": "Request timeout",
            "mode": "aws"
        }
    except requests.exceptions.RequestException as e:
        print(f"[AWS LAMBDA] Connection error: {str(e)}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "response_text": f"❌ Ulanish xatosi: {str(e)}",
            "buttons": None,
            "error": str(e),
            "mode": "aws"
        }
    except Exception as e:
        print(f"[AWS LAMBDA] Error: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "response_text": f"❌ Lambda xatosi: {str(e)}",
            "buttons": None,
            "error": str(e),
            "mode": "aws"
        }


# ============= ENDPOINTS =============
@app.get("/", tags=["Health"])
async def health():
    """Health check"""
    return {
        "status": "ok",
        "simulator": "running",
        "lambda_url": LAMBDA_WEBHOOK_URL,
        "local_mode_available": LAMBDA_AVAILABLE,
        "modes": ["local", "aws"] if LAMBDA_AVAILABLE else ["aws"]
    }


@app.post("/send-message", tags=["Chat"])
async def send_message(request: MessageRequest):
    """
    Frontend sends message to bot via Simulator
    
    Can call in two modes:
    1. local - Call lambda_function.lambda_handler directly (testing)
    2. aws - Call real AWS Lambda webhook (production)
    
    Flow:
    1. Create Telegram-like update from user message
    2. Send to Lambda (local or AWS)
    3. Lambda processes it
    4. Lambda returns response
    5. Extract bot response and return to frontend
    """
    try:
        # Create REAL Telegram-like update
        update = create_telegram_update(request.user_id, request.text)
        
        print(f"[SIMULATOR] Mode: {request.mode}")
        print(f"[SIMULATOR] User ID: {request.user_id}, Message: {request.text}")
        
        # Route to appropriate Lambda
        if request.mode == "local":
            result = call_local_lambda(update)
        else:  # aws
            result = call_aws_lambda(update)
        
        return result
    
    except Exception as e:
        print(f"[SIMULATOR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-callback", tags=["Chat"])
async def send_callback(request: CallbackRequest):
    """
    Frontend sends callback (button click) to bot via Simulator
    
    Can call in two modes:
    1. local - Call lambda_function.lambda_handler directly (testing)
    2. aws - Call real AWS Lambda webhook (production)
    
    Flow:
    1. Create Telegram-like callback_query update
    2. Send to Lambda (local or AWS)
    3. Lambda processes it
    4. Lambda returns response
    5. Return bot's reply to frontend
    """
    try:
        # Create REAL Telegram-like callback update
        update = create_callback_update(request.user_id, request.callback_data)
        
        print(f"[SIMULATOR] Mode: {request.mode}")
        print(f"[SIMULATOR] User ID: {request.user_id}, Callback: {request.callback_data}")
        
        # Route to appropriate Lambda
        if request.mode == "local":
            result = call_local_lambda(update)
        else:  # aws
            result = call_aws_lambda(update)
        
        return result
    
    except Exception as e:
        print(f"[SIMULATOR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
