import json
import os
import requests
import traceback
from datetime import datetime


# ============= BUG HUNTER LOGGER =============
class BugHunter:
    """Send critical errors to Telegram bot for monitoring"""
    
    def __init__(self):
        self.token = os.environ.get("BUG_HUNTER_BOT_TOKEN")
        self.chat_id = os.environ.get("BUG_HUNTER_CHAT_ID", "")
        self.enabled = bool(self.token and self.chat_id)
    
    def log_error(self, error_type: str, error_msg: str, stack_trace: str = "", context_data: dict = None):
        """Log error to Telegram bot with details"""
        if not self.enabled:
            print(f"[BUG_HUNTER] ⚠️  Not configured (token/chat_id missing) - Error: {error_type}")
            return False
        
        try:
            timestamp = datetime.now().isoformat()
            
            # Log to console first
            print(f"[BUG_HUNTER] 🚨 Reporting {error_type} to Telegram...")
            
            # Prepare detailed log message (for file)
            detailed_log = f"""
🚨 BUG ALERT 🚨
═══════════════════════════════════════════
Timestamp: {timestamp}
Error Type: {error_type}
Message: {error_msg}

Stack Trace:
─────────────────────────────────────────────
{stack_trace}

Context Data:
─────────────────────────────────────────────
{json.dumps(context_data or {}, indent=2, ensure_ascii=False)}
═══════════════════════════════════════════
"""
            
            # Prepare short message for Telegram (message size limited to 4096)
            short_msg = f"""🚨 ERROR DETECTED 🚨

*Type:* `{error_type}`
*Time:* `{timestamp}`

*Error:*
```
{error_msg[:200]}
```

*Details:* See attached file or CloudWatch logs
"""
            
            # Send to Telegram bot
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": short_msg,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"[BUG_HUNTER] ✅ {error_type} sent to Telegram successfully")
                return True
            else:
                print(f"[BUG_HUNTER] ❌ Failed to send {error_type} to Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[BUG_HUNTER] Error in bug reporting: {str(e)}")
            return False


# ============= APPLICATION LAYER =============
class BotApplication:
    """Application layer - business logic for bot responses"""
    
    @staticmethod
    def handle_start_command(user_id, user_first_name=None):
        """Handle /start command"""
        name = user_first_name or "Foydalanuvchi"
        return f"Assalomu alaikum {name}! 👋\n\nMen sizning assistant botingiman. Men bilan ham qanday ishlashni keyinroq bilib olasiz!"
    
    @staticmethod
    def handle_help_command():
        """Handle /help command"""
        return """📖 Mening buyruqlarim:

/start - Boshlang'ich xabar
/help - Bu xabar
/info - Men haqimda ma'lumot
/echo <text> - Xabarni takrorlash

Shuningdek, qayta ishlanuvchi tugmalar bilan o'ynay olasiz! 🎮"""
    
    @staticmethod
    def handle_info_command():
        """Handle /info command"""
        return """ℹ️ Men haqimda:

Men aiogramda yozilgan bot.
Webhook rejimida ishlayman.
Serverless infrastructureda (AWS Lambda) joylashtirildim.

Muloqotingiz uchun rahmat! ❤️"""
    
    @staticmethod
    def handle_echo_message(text):
        """Echo user's message"""
        return f"Siz yuborganingiz: {text} ✅"
    
    @staticmethod
    def handle_callback(callback_data):
        """Handle callback button presses"""
        callbacks = {
            "btn_hello": "Salom! 👋",
            "btn_help": "Yordam kerakmi? /help buyrug'ini kiriting",
            "btn_info": "Info uchun /info buyrug'ini kiriting"
        }
        return callbacks.get(callback_data, "Noma'lum tugma 🤔")


# ============= ENVIRONMENT LAYER =============
class TelegramEnvironment:
    """Environment layer - Telegram API communication"""
    
    def __init__(self, is_simulator=False):
        self.bot_token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.is_simulator = is_simulator
        self.app = BotApplication()
        self.responses = []  # Store responses for tracking
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Send message via Telegram API or store for simulator"""
        message_data = {
            "chat_id": chat_id,
            "text": text,
            "method": "sendMessage"
        }
        
        if self.is_simulator:
            print(f"[SIMULATOR] Sending to {chat_id}: {text}")
            self.responses.append(message_data)
            return {"success": True, "response_text": text}
        
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.responses.append(message_data)
            
            return {
                "success": response.status_code == 200,
                "response_text": text,
                "status_code": response.status_code
            }
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            stack_trace = traceback.format_exc()
            print(error_msg)
            print(stack_trace)
            
            # Log to bug hunter bot
            bug_hunter = BugHunter()
            bug_hunter.log_error(
                error_type="SEND_MESSAGE_ERROR",
                error_msg=error_msg,
                stack_trace=stack_trace,
                context_data={
                    "chat_id": chat_id,
                    "text_length": len(text),
                    "has_reply_markup": reply_markup is not None
                }
            )
            
            return {
                "success": False,
                "response_text": f"Xato: {str(e)}",
                "error": str(e)
            }
    
    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Answer callback query (button click notification)"""
        if self.is_simulator:
            print(f"[SIMULATOR] Callback answer: {text}")
            self.responses.append({
                "method": "answerCallbackQuery",
                "callback_query_id": callback_query_id,
                "text": text
            })
            return True
        
        try:
            payload = {
                "callback_query_id": callback_query_id,
                "show_alert": show_alert
            }
            
            if text:
                payload["text"] = text
            
            response = requests.post(
                f"{self.api_url}/answerCallbackQuery",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            error_msg = f"Error answering callback: {str(e)}"
            stack_trace = traceback.format_exc()
            print(error_msg)
            print(stack_trace)
            
            # Log to bug hunter bot
            bug_hunter = BugHunter()
            bug_hunter.log_error(
                error_type="CALLBACK_QUERY_ERROR",
                error_msg=error_msg,
                stack_trace=stack_trace,
                context_data={
                    "callback_query_id": callback_query_id,
                    "text": text
                }
            )
            
            return False


# ============= ADAPTER LAYER =============
class TelegramAdapter:
    """
    Adapter layer - bridges Lambda webhook events to bot logic
    Routes updates to appropriate handlers (commands, callbacks, messages)
    """
    
    def __init__(self, is_simulator=False):
        self.is_simulator = is_simulator
        self.env = TelegramEnvironment(is_simulator=is_simulator)
    
    def _get_start_keyboard(self):
        """Generate start command keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": "👋 Salom", "callback_data": "btn_hello"},
                    {"text": "❓ Yordam", "callback_data": "btn_help"}
                ],
                [
                    {"text": "ℹ️ Info", "callback_data": "btn_info"}
                ]
            ]
        }
    
    def process_update(self, update_dict):
        """
        Process incoming webhook update
        Routes to message handler, command handler, or callback handler
        
        Args:
            update_dict: Raw Telegram update dictionary
            
        Returns:
            Processing result with response
        """
        try:
            # Handle message updates
            if "message" in update_dict:
                return self._handle_message(update_dict["message"])
            
            # Handle callback query updates (button clicks)
            elif "callback_query" in update_dict:
                return self._handle_callback_query(update_dict["callback_query"])
            
            # Other updates are ignored (channel posts, edited messages, etc.)
            else:
                return {
                    "success": True,
                    "message": "Update type not handled (ignored)",
                    "is_simulator": self.is_simulator
                }
        
        except Exception as e:
            error_msg = f"Update processing failed: {str(e)}"
            stack_trace = traceback.format_exc()
            print(f"[ERROR] {error_msg}")
            print(stack_trace)
            
            # Log to bug hunter bot
            bug_hunter = BugHunter()
            bug_hunter.log_error(
                error_type="UPDATE_PROCESSING_ERROR",
                error_msg=error_msg,
                stack_trace=stack_trace,
                context_data={
                    "update_type": type(update_dict).__name__,
                    "update_keys": list(update_dict.keys()) if isinstance(update_dict, dict) else None
                }
            )
            
            return {
                "success": False,
                "message": str(e),
                "error": str(e),
                "is_simulator": self.is_simulator
            }
    
    def _handle_message(self, message):
        """Handle incoming message updates"""
        try:
            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")
            user_first_name = message.get("from", {}).get("first_name")
            text = message.get("text", "").strip()
            
            if not text:
                return {"success": True, "message": "Empty message ignored"}
            
            response_text = None
            keyboard = None
            
            # Route to command or message handler
            if text.startswith("/"):
                
                # Command message
                command = text.split()[0]  # /start, /help, /echo, etc.
                
                if command == "/start":
                    response_text = self.env.app.handle_start_command(user_id, user_first_name)
                    keyboard = self._get_start_keyboard()
                
                elif command == "/help":
                    response_text = self.env.app.handle_help_command()
                    BugHunter().log_error(error_type="NO_ERROR", error_msg=text, context_data=response_text)
                
                elif command == "/info":
                    response_text = self.env.app.handle_info_command()
                
                elif command == "/echo":
                    # /echo <text>
                    parts = text.split(maxsplit=1)
                    if len(parts) < 2:
                        response_text = "Foydalanish: /echo <sizning xabaringiz>"
                    else:
                        response_text = self.env.app.handle_echo_message(parts[1])
                
                else:
                    # Unknown command
                    response_text = f"Noma'lum buyruq: {command}\n/help buyrug'ini kiriting"
            
            else:
                # Regular text message - echo it
                response_text = self.env.app.handle_echo_message(text)
            
            # Send response
            buttons = None
            if response_text:
                self.env.send_message(
                    chat_id,
                    response_text,
                    reply_markup=keyboard
                )
                if keyboard:
                    buttons = keyboard
            
            return {
                "success": True,
                "message": "Message processed",
                "response_text": response_text,
                "buttons": buttons,
                "is_simulator": self.is_simulator,
                "responses": self.env.responses if self.is_simulator else []
            }
        
        except Exception as e:
            error_msg = f"Message handling failed: {str(e)}"
            stack_trace = traceback.format_exc()
            print(f"[ERROR] {error_msg}")
            print(stack_trace)
            
            # Log to bug hunter bot
            bug_hunter = BugHunter()
            bug_hunter.log_error(
                error_type="MESSAGE_HANDLER_ERROR",
                error_msg=error_msg,
                stack_trace=stack_trace,
                context_data={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "text": text[:100] if text else None
                }
            )
            
            return {
                "success": False,
                "message": str(e),
                "error": str(e),
                "is_simulator": self.is_simulator
            }
    
    def _handle_callback_query(self, callback_query):
        """Handle callback query updates (button clicks)"""
        try:
            callback_id = callback_query.get("id")
            callback_data = callback_query.get("data", "")
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            
            # Get response text for this callback
            response_text = self.env.app.handle_callback(callback_data)
            
            # Answer the callback query (show notification)
            self.env.answer_callback_query(callback_id, response_text, show_alert=False)
            
            # Send response message
            if chat_id:
                self.env.send_message(chat_id, response_text)
            
            return {
                "success": True,
                "message": "Callback processed",
                "response_text": response_text,
                "buttons": None,
                "is_simulator": self.is_simulator,
                "responses": self.env.responses if self.is_simulator else []
            }
        
        except Exception as e:
            error_msg = f"Callback handling failed: {str(e)}"
            stack_trace = traceback.format_exc()
            print(f"[ERROR] {error_msg}")
            print(stack_trace)
            
            # Log to bug hunter bot
            bug_hunter = BugHunter()
            bug_hunter.log_error(
                error_type="CALLBACK_HANDLER_ERROR",
                error_msg=error_msg,
                stack_trace=stack_trace,
                context_data={
                    "callback_id": callback_id,
                    "callback_data": callback_data,
                    "chat_id": chat_id
                }
            )
            
            return {
                "success": False,
                "message": str(e),
                "error": str(e),
                "is_simulator": self.is_simulator
            }


# ============= LAMBDA HANDLER =============
def lambda_handler(event, context):
    """
    AWS Lambda handler for Telegram webhook
    
    Architecture:
    - Lambda receives webhook event from Telegram
    - Adapter routes to appropriate handler (message, command, callback)
    - Environment sends response via Telegram API
    - Returns success status to Lambda
    
    Flow:
    1. Parse incoming webhook event
    2. Check if simulator request (X-Simulator header)
    3. Create adapter with simulator flag
    4. Process update through adapter
    5. Adapter routes to command/message/callback handler
    6. Handler processes through application layer
    7. Environment sends response via Telegram API
    8. Return result to Lambda
    """
    try:
        # Parse incoming webhook event
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        # Check if request is from simulator
        headers = event.get("headers", {})
        is_simulator = headers.get("X-Simulator", "").lower() == "true"
        
        # Process update through adapter
        adapter = TelegramAdapter(is_simulator=is_simulator)
        result = adapter.process_update(body)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "result": "ok",
                "message": "Webhook processed successfully",
                "details": result
            }),
        }
    
    except Exception as e:
        error_msg = f"Lambda handler error: {str(e)}"
        stack_trace = traceback.format_exc()
        print(f"[LAMBDA ERROR] {error_msg}")
        print(stack_trace)
        
        # Log critical error to bug hunter bot
        bug_hunter = BugHunter()
        bug_hunter.log_error(
            error_type="LAMBDA_HANDLER_CRITICAL_ERROR",
            error_msg=error_msg,
            stack_trace=stack_trace,
            context_data={
                "request_type": "Telegram webhook",
                "event_keys": list(event.keys()) if isinstance(event, dict) else None
            }
        )
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "result": "error",
                "message": str(e)
            }),
        }
