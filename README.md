# Library Service API

Online management system for book borrowings — REST API built with Django REST Framework + React frontend.

## Features

- JWT authentication with custom `Authorize` header
- Books inventory management (CRUD)
- Borrowing system with automatic inventory tracking
- Stripe payment integration (payments and fines)
- Telegram notifications (new borrowings, overdue alerts)
- Scheduled daily overdue check via Celery Beat
- Pending payment check before new borrowing
- Swagger/OpenAPI documentation
- React SPA frontend

## Tech Stack

### Backend
- Python 3.12 / Django 6.x / Django REST Framework
- PostgreSQL
- Redis (Celery broker)
- Celery + Celery Beat (async tasks, scheduling)
- Stripe API (payments)
- Telegram Bot API (notifications)
- drf-spectacular (Swagger)
- Docker + docker-compose

### Frontend
- React 19 + TypeScript
- Vite
- Axios (API client with JWT auto-refresh)
- React Router

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Stripe account (test mode) — [dashboard.stripe.com](https://dashboard.stripe.com)
- Telegram bot token — create via [@BotFather](https://t.me/BotFather)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Gennadiy-Zubariev/library-service.git
cd library-service
```

2. Create `.env` file from sample:
```bash
cp .env_sample .env
```

3. Fill in your `.env`:
```env
DJANGO_SECRET_KEY=your-secret-key
POSTGRES_DB=library_db
POSTGRES_USER=library_user
POSTGRES_PASSWORD=library_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
DJANGO_SETTINGS_MODULE=config.settings.dev
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

4. Build and run backend:
```bash
docker compose up --build
```

5. Create superuser:
```bash
docker compose exec web python manage.py createsuperuser
```

6. Run frontend (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

The API is available at `http://localhost:8000/api/`
The frontend is available at `http://localhost:5173/`

## API Endpoints

### Users
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | /api/users/register/ | Register new user | Public |
| POST | /api/users/token/ | Get JWT tokens | Public |
| POST | /api/users/token/refresh/ | Refresh access token | Public |
| GET | /api/users/me/ | Get profile | Authenticated |
| PUT/PATCH | /api/users/me/ | Update profile | Authenticated |

### Books
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | /api/books/ | List books | Public |
| GET | /api/books/\<id\>/ | Book detail | Public |
| POST | /api/books/ | Create book | Admin |
| PUT/PATCH | /api/books/\<id\>/ | Update book | Admin |
| DELETE | /api/books/\<id\>/ | Delete book | Admin |

### Borrowings
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | /api/borrowings/ | List borrowings | Authenticated |
| GET | /api/borrowings/\<id\>/ | Borrowing detail | Authenticated |
| POST | /api/borrowings/ | Create borrowing | Authenticated |
| POST | /api/borrowings/\<id\>/return/ | Return book | Authenticated |

Borrowing list supports filtering:
- `?is_active=true` — only active (not returned) borrowings
- `?user_id=1` — filter by user (admin only)

### Payments
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | /api/payments/ | List payments | Authenticated |
| GET | /api/payments/\<id\>/ | Payment detail | Authenticated |
| GET | /api/payments/success/?session_id=... | Confirm payment | Authenticated |
| GET | /api/payments/cancel/ | Cancel payment | Authenticated |

## Authentication

The API uses JWT tokens with a custom header `Authorize` (not the standard `Authorization`).

1. Get tokens: `POST /api/users/token/` with `{"email": "...", "password": "..."}`
2. Use access token: add header `Authorize: Bearer <access_token>`
3. Refresh: `POST /api/users/token/refresh/` with `{"refresh": "<refresh_token>"}`

## Borrowing & Payment Flow

1. User creates a borrowing → book inventory decreases by 1
2. Stripe Checkout session is created automatically → Payment (PENDING)
3. User opens `session_url` and pays → redirected to success page → Payment becomes PAID
4. User returns the book → inventory increases by 1
5. If returned late → a FINE payment is created (daily_fee × days_overdue × 2)

Users cannot create new borrowings while they have pending payments.

## Notifications

Telegram notifications are sent for:
- New borrowing created
- Overdue borrowings (daily check at 9:00)
- Successful payment

## Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | / | Welcome page after login |
| Login | /login | Email + password authentication |
| Register | /register | New user registration |
| Books | /books | Browse all books (public) |
| Book Detail | /books/:id | View/edit/delete book (admin) |
| Add Book | /books/create | Create new book (admin) |
| My Borrowings | /borrowings | List with active/user filters |
| New Borrowing | /borrowings/create | Select book + return date |
| Borrowing Detail | /borrowings/:id | Details, return, payments |
| Profile | /profile | View/edit user profile |
| Payment Success | /payments/success | Stripe payment confirmation |
| Payment Cancel | /payments/cancel | Payment postponed message |

## API Documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Running Tests

```bash
python manage.py test
```

With coverage:
```bash
coverage run --source='.' manage.py test
coverage report --show-missing
```

## Architecture

```
Frontend (React SPA, port 5173)
  ↓ Axios + JWT
Backend (Django REST Framework, port 8000)
├── Users Service      — authentication, registration
├── Books Service      — book inventory CRUD
├── Borrowings Service — borrow/return books
├── Payments Service   — Stripe integration
└── Notifications      — Telegram bot

Celery Worker ← Redis ← Celery Beat
└── Async Telegram notifications
└── Daily overdue check (9:00)

PostgreSQL — data storage
Redis — message broker
```

## Docker Services

| Service | Description |
|---------|-------------|
| web | Django application |
| db | PostgreSQL 16 |
| redis | Redis 7 (Celery broker) |
| celery_worker | Executes async tasks |
| celery_beat | Schedules periodic tasks |

## Test Stripe Card

For testing payments use: `4242 4242 4242 4242`, any future expiry, any CVC.
