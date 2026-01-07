#!/usr/bin/env python3
"""
Telegram Webhook Server with Automatic ngrok Setup
Runs Lambda function locally and manages Telegram webhook automatically
"""

import os
import json
import signal
import sys
import atexit
import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from dotenv import load_dotenv

# Import lambda handler
try:
    from lambda_function import lambda_handler
    LAMBDA_AVAILABLE = True
except ImportError:
    LAMBDA_AVAILABLE = False
    print("[ERROR] Could not import lambda_handler from lambda_function.py")

# Load environment variables from .env
load_dotenv()

# ============= CONFIGURATION =============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "7172"))
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "0.0.0.0")

# Cache file for webhook state
WEBHOOK_CACHE_FILE = Path(__file__).parent / ".webhook_cache.json"

# FastAPI app
app = FastAPI(title="Telegram Webhook", version="1.0.0")

# Global state
webhook_state = {
    "ngrok_url": None,
    "old_webhook_url": None,
    "needs_cleanup": False,
}


# ============= WEBHOOK CACHE MANAGEMENT =============
def load_webhook_cache() -> Optional[Dict[str, str]]:
    """Load cached webhook information"""
    try:
        if WEBHOOK_CACHE_FILE.exists():
            with open(WEBHOOK_CACHE_FILE, 'r') as f:
                data = json.load(f)
                print(f"[CACHE] Loaded cached webhook: {data.get('url', 'unknown')}")
                return data
    except Exception as e:
        print(f"[CACHE] Error loading cache: {e}")
    return None


def save_webhook_cache(webhook_info: Dict[str, str]):
    """Save webhook information to cache"""
    try:
        with open(WEBHOOK_CACHE_FILE, 'w') as f:
            json.dump(webhook_info, f, indent=2)
            print(f"[CACHE] Saved webhook cache: {webhook_info.get('url', 'unknown')}")
    except Exception as e:
        print(f"[CACHE] Error saving cache: {e}")


def clear_webhook_cache():
    """Clear webhook cache file"""
    try:
        if WEBHOOK_CACHE_FILE.exists():
            WEBHOOK_CACHE_FILE.unlink()
            print("[CACHE] ✅ Webhook cache cleared")
    except Exception as e:
        print(f"[CACHE] Error clearing cache: {e}")


# ============= TELEGRAM API HELPERS =============
def get_webhook_info() -> Optional[Dict[str, Any]]:
    """Get current webhook info from Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                print(f"[TELEGRAM] Current webhook: {webhook_info.get('url', 'none')}")
                return webhook_info
        else:
            print(f"[TELEGRAM] getWebhookInfo failed: {response.status_code}")
    except Exception as e:
        print(f"[TELEGRAM] Error getting webhook info: {e}")
    
    return None


def delete_webhook() -> bool:
    """Delete current webhook from Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("[TELEGRAM] ✅ Webhook deleted successfully")
                return True
        
        print(f"[TELEGRAM] deleteWebhook failed: {response.status_code}")
    except Exception as e:
        print(f"[TELEGRAM] Error deleting webhook: {e}")
    
    return False


def set_webhook(webhook_url: str) -> bool:
    """Set webhook URL in Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        payload = {"url": webhook_url}
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print(f"[TELEGRAM] ✅ Webhook set: {webhook_url}")
                return True
        
        print(f"[TELEGRAM] setWebhook failed: {response.status_code}")
        print(f"[TELEGRAM] Response: {response.text}")
    except Exception as e:
        print(f"[TELEGRAM] Error setting webhook: {e}")
    
    return False


# ============= NGROK MANAGEMENT =============
def get_ngrok_url() -> Optional[str]:
    """Get public URL from ngrok"""
    try:
        # ngrok exposes API on localhost:4040
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    url = tunnel.get('public_url')
                    if url:
                        print(f"[NGROK] Public URL: {url}")
                        return url
        
        print("[NGROK] No HTTPS tunnel found")
    except Exception as e:
        print(f"[NGROK] Error getting ngrok URL: {e}")
    
    return None


# ============= WEBHOOK SETUP/CLEANUP =============
def setup_webhook():
    """Set up webhook with ngrok"""
    global webhook_state
    
    if not BOT_TOKEN:
        print("[SETUP] ❌ BOT_TOKEN not configured in .env")
        return False
    
    print("\n" + "="*60)
    print("[SETUP] Starting webhook configuration...")
    print("="*60)
    
    # Step 1: Get current webhook info
    print("[SETUP] Step 1: Checking current webhook...")
    current_webhook = get_webhook_info()
    current_webhook_url = current_webhook.get('url') if current_webhook else None
    
    # Save current webhook as old webhook (to restore later)
    if current_webhook_url:
        webhook_state["old_webhook_url"] = current_webhook_url
        print(f"[SETUP] Current webhook will be restored on cleanup: {current_webhook_url}")
    
    # Step 2: Load cached webhook if exists (backup in case)
    print("[SETUP] Step 2: Loading cached webhook...")
    cached_webhook = load_webhook_cache()
    
    if cached_webhook and not webhook_state["old_webhook_url"]:
        webhook_state["old_webhook_url"] = cached_webhook.get("url")
        print(f"[SETUP] Using cached webhook: {webhook_state['old_webhook_url']}")
    
    # Step 3: Delete current webhook if running
    print("[SETUP] Step 3: Deleting current webhook...")
    if current_webhook_url:
        delete_webhook()
        time.sleep(1)
    
    # Step 4: Wait for ngrok to start
    print("[SETUP] Step 4: Waiting for ngrok tunnel...")
    max_retries = 10
    for i in range(max_retries):
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            webhook_state["ngrok_url"] = ngrok_url
            webhook_state["needs_cleanup"] = True
            break
        
        if i < max_retries - 1:
            print(f"[SETUP] Retrying... ({i+1}/{max_retries})")
            time.sleep(1)
    
    if not webhook_state["ngrok_url"]:
        print("[SETUP] ❌ Could not get ngrok URL")
        print("[SETUP] Make sure ngrok is running: ngrok http 7172")
        return False
    
    # Step 5: Set new webhook
    print("[SETUP] Step 5: Setting new webhook...")
    if set_webhook(webhook_state["ngrok_url"]):
        # Save old webhook URL to cache (for restoration on next run)
        save_webhook_cache({
            "url": webhook_state["old_webhook_url"],
            "timestamp": str(time.time())
        })
        
        print("\n" + "="*60)
        print("✅ WEBHOOK SETUP COMPLETE")
        print("="*60)
        print(f"Webhook URL (ngrok): {webhook_state['ngrok_url']}")
        print(f"Production URL (cached): {webhook_state['old_webhook_url'] or 'None'}")
        print(f"Local Port: {WEBHOOK_PORT}")
        print("="*60 + "\n")
        return True
    
    return False


def cleanup_webhook():
    """Clean up webhook on shutdown"""
    global webhook_state
    
    if not webhook_state["needs_cleanup"]:
        print("[CLEANUP] No cleanup needed")
        return
    
    print("\n" + "="*60)
    print("[CLEANUP] Cleaning up webhook...")
    print("="*60)
    
    # Step 1: Delete ngrok webhook
    if webhook_state["ngrok_url"]:
        print("[CLEANUP] Step 1: Deleting ngrok webhook...")
        delete_webhook()
        time.sleep(1)
    
    # Step 2: Restore old webhook if cached
    if webhook_state["old_webhook_url"]:
        print(f"[CLEANUP] Step 2: Restoring old webhook...")
        if set_webhook(webhook_state["old_webhook_url"]):
            print(f"[CLEANUP] ✅ Restored: {webhook_state['old_webhook_url']}")
        time.sleep(1)
    
    # Step 3: Clear cache
    print("[CLEANUP] Step 3: Clearing cache...")
    clear_webhook_cache()
    
    print("="*60)
    print("✅ CLEANUP COMPLETE")
    print("="*60 + "\n")


# ============= SIGNAL HANDLERS =============
def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[SIGNAL] Received Ctrl+C, cleaning up...")
    cleanup_webhook()
    sys.exit(0)


# ============= FASTAPI ENDPOINTS =============
@app.get("/", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "webhook": webhook_state["ngrok_url"] or "not configured",
        "lambda_available": LAMBDA_AVAILABLE,
        "port": WEBHOOK_PORT
    }


@app.post("/", tags=["Webhook"])
async def handle_webhook(request: Request):
    """
    Main webhook endpoint - receives updates from Telegram
    Forwards to lambda_handler
    """
    if not LAMBDA_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Lambda handler not available"}
        )
    
    try:
        # Get JSON body
        body = await request.json()
        
        print(f"\n[WEBHOOK] Received update: {body.get('update_id', 'unknown')}")
        
        # Create Lambda event
        event = {
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "X-Simulator": "false"
            }
        }
        
        # Call lambda handler
        result = lambda_handler(event, context=None)
        
        print(f"[WEBHOOK] Response: {result.get('statusCode', 'unknown')}")
        
        # Return response
        if result.get("statusCode") == 200:
            return JSONResponse(
                status_code=200,
                content={"result": "ok"}
            )
        else:
            return JSONResponse(
                status_code=result.get("statusCode", 500),
                content=result.get("body", {})
            )
    
    except Exception as e:
        print(f"[WEBHOOK] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/status", tags=["Debug"])
async def status():
    """Get webhook status"""
    webhook_info = get_webhook_info()
    return {
        "ngrok_url": webhook_state["ngrok_url"],
        "old_webhook_url": webhook_state["old_webhook_url"],
        "telegram_webhook": webhook_info,
        "needs_cleanup": webhook_state["needs_cleanup"],
        "lambda_available": LAMBDA_AVAILABLE
    }


# ============= MAIN =============
if __name__ == "__main__":
    # Register cleanup on exit
    atexit.register(cleanup_webhook)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup webhook
    if not setup_webhook():
        print("[ERROR] Failed to setup webhook")
        sys.exit(1)
    
    # Start server
    print(f"\n[SERVER] Starting on {WEBHOOK_HOST}:{WEBHOOK_PORT}...\n")
    print("Press Ctrl+C to shutdown and cleanup webhook\n")
    
    try:
        uvicorn.run(
            app,
            host=WEBHOOK_HOST,
            port=WEBHOOK_PORT,
            log_level="info"
        )
    except KeyboardInterrupt:
        cleanup_webhook()
        sys.exit(0)
