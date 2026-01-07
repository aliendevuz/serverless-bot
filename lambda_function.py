import json
from adapter import TelegramAdapter


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
