# Telegram Bot Simulator

Telegram botni local muhitda testing qilish uchun FastAPI + React simulator.

## Struktura

```
simulator/
  ├── main.py              # FastAPI server
  ├── mock_data.json       # Mock user va chat data
  ├── requirements.txt     # Python dependencies
  └── frontend/            # React UI
      ├── package.json
      ├── ChatUI.jsx
      ├── ChatUI.css
      ├── App.jsx
      ├── index.js
      └── public/
          └── index.html
```

## O'rnatish

### FastAPI Backend

```bash
cd simulator
pip install -r requirements.txt
```

### React Frontend

```bash
cd simulator/frontend
npm install
```

## Ishga tushirish

### Backend (Port 8000)

```bash
cd simulator
python main.py
```

Yoki:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend (Port 3000)

```bash
cd simulator/frontend
npm start
```

Browser `http://localhost:3000` da ochiladi

## Ishchi jarayoni

1. **Frontend**: Foydalanuvchini tanlab, xabar yuboring
2. **FastAPI**: Telegramga o'xshash update JSON yaratib, Lambda webhookga yuboradi
3. **Lambda**: Simulator ekanligini biladi (`X-Simulator` header), adapter ni chaqiradi
4. **Adapter**: Environment orqali application ni chaqiradi
5. **Application**: Xabarni process qiladi
6. **Environment**: Simulatorga (haqiqiy API emas) javob qaytaradi
7. **Frontend**: Javobni render qiladi

## API Endpoints

- `GET /` - Health check
- `GET /users` - Barcha mock users
- `GET /users/{user_id}` - Specific user
- `POST /send-message` - Xabar yuborish
- `GET /webhook-test` - Webhook test

## Environment Variables

```bash
# FastAPI
LAMBDA_WEBHOOK_URL=https://vwn78888d8.execute-api.eu-central-1.amazonaws.com/main
SIMULATOR_URL=http://localhost:8000

# Lambda (aws environment)
BOT_TOKEN=your_bot_token_here
```

## Mock Data Format

`mock_data.json` da real user/chat datani saqlang:

```json
{
  "users": [
    {
      "id": 123,
      "first_name": "Ism",
      "username": "username"
    }
  ],
  "chats": [
    {
      "id": 123,
      "type": "private",
      "first_name": "Ism",
      "username": "username"
    }
  ]
}
```

## Frontend Environment

`.env` faylni frontend papkasiga qo'shing:

```
REACT_APP_SIMULATOR_URL=http://localhost:8000
```

## Debugging

FastAPI logs:

```
[SIMULATOR] Message queued for user 123: Siz yuborganingiz: Salom ✅
```

Browser DevTools da network requestlarni ko'ring.

## Notes

- Simulator faqat development uchun
- Mock data haqiqiy userData ni o'xshaydi
- Inline reply buttons yo'li bilan qo'shimcha feature qo'shish mumkin
