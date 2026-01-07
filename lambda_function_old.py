import json
import os
import requests
from aiogram import Dispatcher, Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Update


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
        if callback_data == "btn_hello":
            return "Salom! 👋"
        elif callback_data == "btn_help":
            return "Yordam kerakmi? /help buyrug'ini kiriting"
        elif callback_data == "btn_info":
            return "Info uchun /info buyrug'ini kiriting"
        return "Noma'lum tugma 🤔"


# ============= ENVIRONMENT LAYER =============
class TelegramEnvironment:
    """Environment layer - Telegram API communication"""
    
    def __init__(self, is_simulator=False):
        self.bot_token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.is_simulator = is_simulator
        self.app = BotApplication()
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Send message via Telegram API"""
        if self.is_simulator:
            # Simulator faqat response_text qaytaradi
            print(f"[SIMULATOR] Message to {chat_id}: {text}")
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
            
            return {
                "success": response.status_code == 200,
                "response_text": text,
                "status_code": response.status_code
            }
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "response_text": f"Xato: {str(e)}",
                "error": str(e)
            }
    
    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Answer callback query (button click)"""
        if self.is_simulator:
            print(f"[SIMULATOR] Callback answer: {text}")
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
            print(f"Error answering callback: {str(e)}")
            return False


# ============= ADAPTER LAYER =============
class TelegramAdapter:
    """
    Adapter layer - bridges Lambda webhook events to aiogram
    Handles event routing and processing
    """
    
    def __init__(self, is_simulator=False):
        self.is_simulator = is_simulator
        self.env = TelegramEnvironment(is_simulator=is_simulator)
        self.router = Router()
        self._setup_handlers()
        self.dp = Dispatcher()
        self.dp.include_router(self.router)
    
    def _setup_handlers(self):
        """Setup aiogram message, command, and callback handlers"""
        
        # /start command handler
        @self.router.message(Command("start"))
        async def cmd_start(message: types.Message):
            text = self.env.app.handle_start_command(
                message.from_user.id,
                message.from_user.first_name
            )
            # Create inline keyboard
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="👋 Salom", callback_data="btn_hello"),
                    types.InlineKeyboardButton(text="❓ Yordam", callback_data="btn_help")
                ],
                [
                    types.InlineKeyboardButton(text="ℹ️ Info", callback_data="btn_info")
                ]
            ])
            
            result = self.env.send_message(message.chat.id, text, keyboard)
            return result
        
        # /help command handler
        @self.router.message(Command("help"))
        async def cmd_help(message: types.Message):
            text = self.env.app.handle_help_command()
            result = self.env.send_message(message.chat.id, text)
            return result
        
        # /info command handler
        @self.router.message(Command("info"))
        async def cmd_info(message: types.Message):
            text = self.env.app.handle_info_command()
            result = self.env.send_message(message.chat.id, text)
            return result
        
        # /echo <text> command handler
        @self.router.message(Command("echo"))
        async def cmd_echo(message: types.Message):
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                text = "Foydalanish: /echo <sizning xabaringiz>"
            else:
                text = self.env.app.handle_echo_message(args[1])
            
            result = self.env.send_message(message.chat.id, text)
            return result
        
        # Callback query handler (button clicks)
        @self.router.callback_query()
        async def process_callback(callback_query: types.CallbackQuery):
            callback_data = callback_query.data
            text = self.env.app.handle_callback(callback_data)
            
            # Answer callback query (notification)
            self.env.answer_callback_query(callback_query.id, text, show_alert=False)
            
            # Edit message or send new message
            result = self.env.send_message(
                callback_query.message.chat.id,
                text
            )
            return result
        
        # Text message handler (fallback)
        @self.router.message()
        async def handle_message(message: types.Message):
            text = self.env.app.handle_echo_message(message.text)
            result = self.env.send_message(message.chat.id, text)
            return result
    
    async def process_update(self, update_dict):
        """
        Process incoming webhook update with aiogram
        
        Args:
            update_dict: Raw Telegram update dictionary
            
        Returns:
            Processing result
        """
        try:
            # Convert dict to aiogram Update object
            update = Update(**update_dict)
            
            # Feed update to dispatcher
            results = await self.dp.feed_update(None, update)
            
            # Extract response from message handler
            response_text = None
            if update.message:
                # Handlers execute and return response
                # We capture it for simulator compatibility
                if hasattr(update.message, '_response'):
                    response_text = update.message._response.get('response_text')
            
            return {
                "success": True,
                "message": "Update processed",
                "response_text": response_text or "Xabaringiz qabul qilindi ✅",
                "is_simulator": self.is_simulator
            }
        
        except Exception as e:
            print(f"[ERROR] Update processing failed: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "error": str(e),
                "is_simulator": self.is_simulator
            }


# ============= LAMBDA HANDLER =============
async def async_lambda_handler(event, context):
    """Async Lambda handler for Telegram webhook"""
    try:
        # Parse webhook event
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        # Check if simulator request
        headers = event.get("headers", {})
        is_simulator = headers.get("X-Simulator", "").lower() == "true"
        
        # Process update through adapter
        adapter = TelegramAdapter(is_simulator=is_simulator)
        result = await adapter.process_update(body)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "result": "ok",
                "message": "Webhook processed",
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


def lambda_handler(event, context):
    """
    Synchronous Lambda handler wrapper for async processing
    AWS Lambda doesn't natively support async, so we wrap it
    """
    import asyncio
    
    try:
        # Create event loop for async processing
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run async handler
    result = loop.run_until_complete(async_lambda_handler(event, context))
    
    return result
