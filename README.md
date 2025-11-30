# Studio Génie Backend

Complete backend system for Studio Génie - UGC AI Video SaaS platform by Brainwash Labs.

## 🚀 Features

- **Authentication**: JWT-based user registration and login
- **Credit System**: Trial videos, credit packs, and subscription plans
- **Video Generation**: Async video generation with Celery workers
- **Payment Integration**: Stripe (subscriptions + one-time) and Coinbase Commerce (crypto with 20% bonus)
- **Storage**: Supabase storage for video files
- **API Documentation**: Auto-generated OpenAPI docs

## 📋 Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT with bcrypt password hashing
- **Payments**: Stripe & Coinbase Commerce
- **Queue**: Celery + Redis
- **Video Processing**: FFmpeg (placeholder for MGX API)
- **Deployment**: Render-ready

## 🏗️ Project Structure

```
studio-genie-backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Settings & environment variables
│   │   ├── database.py        # Supabase client
│   │   └── security.py        # JWT & password utilities
│   ├── api/routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── credits.py         # Credit management
│   │   ├── videos.py          # Video generation & retrieval
│   │   ├── billing.py         # Stripe & Coinbase
│   │   └── subscriptions.py   # Subscription management
│   ├── models/                # Data models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── workers/
│   │   └── celery_worker.py   # Background tasks
│   └── utils/                 # Utilities
├── requirements.txt
├── runtime.txt
├── .env.example
└── postman_collection.json
```

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.11+
- Redis server
- FFmpeg
- Supabase account
- Stripe account
- Coinbase Commerce account (optional)

### 2. Clone and Install

```bash
cd studio-genie-backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required Environment Variables:**

- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- `STRIPE_*_PRICE_ID` (create products in Stripe Dashboard)
- `COINBASE_API_KEY`, `COINBASE_WEBHOOK_SECRET`
- `REDIS_URL`

### 4. Supabase Database Setup

Create the following tables in your Supabase project:

**users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  has_trial_used BOOLEAN DEFAULT FALSE,
  credits_remaining INTEGER DEFAULT 0,
  plan TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**videos**
```sql
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  style TEXT NOT NULL,
  image_url TEXT,
  status TEXT DEFAULT 'queued',
  video_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**payments**
```sql
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  credits_added INTEGER NOT NULL,
  amount_usd NUMERIC(10, 2) NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);
```

**subscriptions**
```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  stripe_sub_id TEXT UNIQUE NOT NULL,
  plan TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5. Create Supabase Storage Bucket

1. Go to Supabase Dashboard → Storage
2. Create a new bucket named `videos`
3. Set it to **public** for easy video access

### 6. Start Redis

```bash
# Windows (using Docker)
docker run -d -p 6379:6379 redis

# Linux/Mac
redis-server
```

### 7. Run the Application

**Terminal 1 - FastAPI Server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.workers.celery_worker worker --loglevel=info
```

### 8. Access the API

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Credits
- `GET /api/v1/credits` - Get credit balance

### Videos
- `POST /api/v1/videos/generate` - Generate new video
- `GET /api/v1/videos` - List user's videos
- `GET /api/v1/videos/{id}` - Get video details
- `GET /api/v1/videos/{id}/download` - Download video

### Billing
- `POST /api/v1/billing/create_checkout_session` - Create Stripe checkout
- `POST /api/v1/billing/create_coinbase_charge` - Create Coinbase charge
- `POST /api/v1/billing/webhook/stripe` - Stripe webhook
- `POST /api/v1/billing/webhook/coinbase` - Coinbase webhook

### Subscriptions
- `GET /api/v1/subscriptions` - List subscriptions
- `GET /api/v1/subscriptions/{id}` - Get subscription details

## 💳 Credit System

- **Trial**: 1 free video per new user
- **Credits per video**: 3 credits
- **Plans**:
  - Starter: 20 credits/month
  - Creator: 50 credits/month
  - Pro: 120 credits/month
- **Coinbase Bonus**: +20% credits on crypto payments

## 🧪 Testing with Postman

Import `postman_collection.json` into Postman:

1. Open Postman
2. Click Import → Upload Files
3. Select `postman_collection.json`
4. Set `base_url` variable to `http://localhost:8000/api/v1`
5. Register/Login to get access token (auto-saved)

## 🚢 Deployment (Render)

### Web Service

1. Create new Web Service on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`

### Background Worker

1. Create new Background Worker on Render
2. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A app.workers.celery_worker worker --loglevel=info`
3. Add same environment variables

### Redis

1. Create Redis instance on Render or use external service
2. Update `REDIS_URL` in environment variables

## 🔐 Webhook Configuration

### Stripe
1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-domain.com/api/v1/billing/webhook/stripe`
3. Select events: `checkout.session.completed`, `invoice.payment_succeeded`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

### Coinbase
1. Go to Coinbase Commerce → Settings → Webhook subscriptions
2. Add endpoint: `https://your-domain.com/api/v1/billing/webhook/coinbase`
3. Copy webhook secret to `COINBASE_WEBHOOK_SECRET`

## 🎬 Video Generation

Currently uses FFmpeg to generate placeholder videos. To integrate MGX API:

1. Update `app/workers/celery_worker.py`
2. Replace `generate_placeholder_video()` with MGX API call
3. Handle MGX response and video URL

## 📝 Notes

- All passwords are hashed with bcrypt
- JWT tokens expire after 30 minutes (configurable)
- Videos are stored in Supabase Storage
- Celery tasks are queued in Redis
- All monetary amounts are in USD

## 🐛 Troubleshooting

**Redis Connection Error:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

**Supabase Connection Error:**
- Verify `SUPABASE_URL` and keys in `.env`
- Check if tables are created

**FFmpeg Not Found:**
```bash
# Install FFmpeg
# Windows: Download from ffmpeg.org
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## 📄 License

Proprietary - Brainwash Labs

## 👥 Support

For issues or questions, contact the Brainwash Labs team.
