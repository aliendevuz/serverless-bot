# Telegram Bot Lambda Webhook Architecture

Modern serverless Telegram bot webhook with layered architecture using AWS Lambda.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (React)                     │
│  - Multiple users                           │
│  - Multiple chats per user                  │
│  - Local storage persistence                │
└────────────────┬────────────────────────────┘
                 │
         ┌───────▼─────────┐
         │ FastAPI Simulator│ (Optional - for testing)
         │   /send-message │
         │ /send-callback  │
         └───────┬─────────┘
                 │
    ┌────────────▼─────────────────┐
    │  AWS Lambda Webhook Handler  │ (lambda_function.py)
    │  ┌──────────────────────────┐│
    │  │ ADAPTER LAYER            ││
    │  │ - Route update type      ││
    │  │ - Message/Callback       ││
    │  └──────────────┬───────────┘│
    │  ┌──────────────▼───────────┐│
    │  │ ENVIRONMENT LAYER        ││
    │  │ - Telegram API calls     ││
    │  │ - Message sending        ││
    │  └──────────────┬───────────┘│
    │  ┌──────────────▼───────────┐│
    │  │ APPLICATION LAYER        ││
    │  │ - Business logic         ││
    │  │ - Command handlers       ││
    │  │ - Message processing     ││
    │  └──────────────────────────┘│
    └────────────────┬─────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Telegram Bot API         │
        │  (Real messages/updates)  │
        └───────────────────────────┘
```

## 🎯 Features

### Commands
- `/start` - Welcome message with inline buttons
- `/help` - List of available commands
- `/info` - Bot information
- `/echo <text>` - Echo user's message

### Update Types Handled
- **Messages** - Text messages, commands
- **Callbacks** - Inline button clicks
- **Ignored** - Other updates (channel posts, edited messages, etc.)

## 📦 Project Structure

```
serverless/
├── lambda_function.py          # Main Lambda handler
├── test_lambda.py             # Local testing script
├── requirements.txt           # Python dependencies
└── simulator/
    ├── main.py               # FastAPI simulator
    ├── frontend/             # React frontend
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── ChatUI.tsx
    │   │   │   └── ChatUI.css
    │   │   └── ...
    │   └── ...
    └── requirements.txt
```

## 🚀 Getting Started

### Local Testing

1. **Run Lambda tests:**
```bash
cd serverless
python test_lambda.py
```

2. **Start simulator:**
```bash
cd simulator
pip install -r requirements.txt
python main.py
```

3. **Open frontend:**
```bash
cd simulator/frontend
npm install
npm run dev
```

### Deploy to AWS Lambda

1. **Package Lambda function:**
```bash
cd serverless
zip -r lambda_function.zip lambda_function.py
```

2. **Create Lambda function:**
```bash
aws lambda create-function \
  --function-name telegram-bot-webhook \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --environment Variables={BOT_TOKEN=YOUR_BOT_TOKEN}
```

3. **Set up webhook in Telegram:**
```bash
curl https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -d "url=https://YOUR_LAMBDA_ENDPOINT/main"
```

## 📝 Code Organization

### Application Layer (`BotApplication`)
Contains business logic for handling different update types:
- Command handlers (`/start`, `/help`, `/info`, `/echo`)
- Callback handlers (button responses)
- Message echo

### Environment Layer (`TelegramEnvironment`)
Handles Telegram API communication:
- Send messages
- Answer callback queries
- Simulator mode support

### Adapter Layer (`TelegramAdapter`)
Routes incoming updates to appropriate handlers:
- Detects update type (message/callback)
- Extracts relevant data
- Calls appropriate handler
- Manages responses

### Lambda Handler
Entry point for AWS Lambda:
- Parses webhook event
- Detects simulator requests (via `X-Simulator` header)
- Instantiates adapter and processes update
- Returns response

## 🧪 Testing

Run local tests without connecting to Telegram:
```bash
python test_lambda.py
```

Tests cover:
- `/start` command
- `/help` command
- `/info` command
- `/echo` command
- Regular text messages
- All callback buttons

## 🔗 API Endpoints

### Simulator Endpoints

**POST /send-message** - Send text message
```json
{
  "user_id": 12345,
  "text": "/start"
}
```

**POST /send-callback** - Send callback (button click)
```json
{
  "user_id": 12345,
  "callback_data": "btn_hello"
}
```

**GET /** - Health check
```json
{
  "status": "ok",
  "simulator": "running",
  "lambda_url": "..."
}
```

## 🛠️ Environment Variables

Set in Lambda function:
- `BOT_TOKEN` - Your Telegram bot token from @BotFather

Optional for simulator:
- `LAMBDA_WEBHOOK_URL` - Override default Lambda endpoint

## 📋 Handling Different Update Types

### Messages
```python
# Detected by: "message" key in update
# Routes to: _handle_message()
# Checks for: Commands (/) or regular text
```

### Callbacks
```python
# Detected by: "callback_query" key in update
# Routes to: _handle_callback_query()
# Calls: answer_callback_query() + send_message()
```

### Ignored Updates
```python
# Channel posts, edited messages, inline queries, etc.
# Acknowledged as success but not processed
```

## 💡 Best Practices

1. **Keep handlers pure** - Don't modify global state
2. **Separate concerns** - App logic ≠ API calls
3. **Error handling** - All exceptions caught and logged
4. **Simulator mode** - Test without Telegram API
5. **Async safety** - Use synchronous code in Lambda

## 📚 References

- [aiogram Documentation](https://aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
