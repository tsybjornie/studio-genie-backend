# Studio Génie Backend - Quick Reference

## 🚀 Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Start services
# Terminal 1: Redis
docker run -d -p 6379:6379 redis

# Terminal 2: API Server
uvicorn app.main:app --reload

# Terminal 3: Celery Worker
celery -A app.workers.celery_worker worker --loglevel=info
```

## 📍 API Endpoints

**Base URL**: `http://localhost:8000/api/v1`

### Auth
- `POST /auth/register` - Register
- `POST /auth/login` - Login
- `GET /auth/me` - User info

### Credits
- `GET /credits` - Balance

### Videos
- `POST /videos/generate` - Generate
- `GET /videos` - List
- `GET /videos/{id}` - Details
- `GET /videos/{id}/download` - Download

### Billing
- `POST /billing/create_checkout_session` - Stripe
- `POST /billing/create_coinbase_charge` - Coinbase
- `POST /billing/webhook/stripe` - Webhook
- `POST /billing/webhook/coinbase` - Webhook

### Subscriptions
- `GET /subscriptions` - List
- `GET /subscriptions/{id}` - Details

## 💳 Credit Plans

| Plan | Credits/Month | Price |
|------|--------------|-------|
| Starter | 20 | Configure in Stripe |
| Creator | 50 | Configure in Stripe |
| Pro | 120 | Configure in Stripe |

**Trial**: 1 free video  
**Cost**: 3 credits per video  
**Coinbase Bonus**: +20% credits

## 🔑 Required Environment Variables

```env
# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# JWT
SECRET_KEY=  # Generate: openssl rand -hex 32

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_STARTER_PRICE_ID=
STRIPE_CREATOR_PRICE_ID=
STRIPE_PRO_PRICE_ID=
STRIPE_CREDIT_PACK_20_PRICE_ID=
STRIPE_CREDIT_PACK_50_PRICE_ID=
STRIPE_CREDIT_PACK_120_PRICE_ID=

# Coinbase
COINBASE_API_KEY=
COINBASE_WEBHOOK_SECRET=

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 📊 Database Tables

Run `database_schema.sql` in Supabase SQL Editor to create:
- `users` - User accounts
- `videos` - Video records
- `payments` - Payment history
- `subscriptions` - Active subscriptions

## 📦 File Structure

```
app/
├── core/           # Config, DB, Security
├── api/routes/     # API endpoints
├── models/         # Data models
├── schemas/        # Request/response schemas
├── services/       # Business logic
├── workers/        # Celery tasks
└── utils/          # Helpers
```

## 🧪 Testing

Import `postman_collection.json` into Postman and test all endpoints.

## 🚢 Deploy to Render

**Web Service**:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Worker**:
- Build: `pip install -r requirements.txt`
- Start: `celery -A app.workers.celery_worker worker --loglevel=info`

Add all environment variables to both services.

## 📝 Notes

- API docs: http://localhost:8000/docs
- FFmpeg required for video generation
- Replace placeholder video function with MGX API
- Configure webhooks in Stripe/Coinbase dashboards
