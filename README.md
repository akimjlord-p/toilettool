# ToiletTool API

Backend service for rating public toilets. Built with FastAPI + PostgreSQL.

## Stack

- **FastAPI** — async REST API
- **PostgreSQL 16** — database
- **SQLAlchemy 2.0** — async ORM
- **Alembic** — migrations
- **OpenAI GPT-4o** — AI-generated comments for tops and monthly winners
- **Docker + Docker Compose** — containerized deployment

## Rating System

Each toilet is rated across 6 criteria with a maximum total score of **90 points**:

| Criterion | Max Score |
|-----------|-----------|
| Cleanliness (surfaces, floor, mirrors) | 25 |
| Supplies (toilet paper, soap, hand dryer) | 20 |
| Smell (odor, ventilation) | 20 |
| Equipment (flush, taps, locks, lighting) | 15 |
| Privacy (stall doors, partitions) | 5 |
| Vibe (general impression) | 5 |

## Project Structure

```
app/
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic request/response schemas
├── repositories/    # Database query layer
├── services/        # Business logic
└── api/v1/          # FastAPI routers
alembic/             # Database migrations
tests/               # pytest test suite
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user profile |
| POST | `/api/v1/users/nickname` | Assign nickname (moderator only) |
| POST | `/api/v1/users/set-moderator` | Grant/revoke moderator role |
| GET | `/api/v1/toilets/search?q=` | Search toilets by address |
| POST | `/api/v1/toilets` | Add a new toilet |
| GET | `/api/v1/toilets/{id}` | Get toilet card with avg scores |
| POST | `/api/v1/reviews` | Submit a review |
| POST | `/api/v1/reviews/moderator` | Submit official moderator review |
| DELETE | `/api/v1/reviews/{id}` | Soft-delete review (moderator only) |
| GET | `/api/v1/top` | Top toilets by criterion |
| GET | `/api/v1/top/month` | Toilet of the month |
| GET | `/api/v1/top/month/history` | Historical monthly winners |
| POST | `/api/v1/top/month/assign` | Assign toilet of the month (moderator only) |

### Authentication

Every request from the Telegram bot must include these headers:

```
X-Telegram-Id: <telegram_user_id>
X-Bot-Secret: <shared_secret>
X-Username: <telegram_username>   # optional
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/toilettool
OPENAI_API_KEY=sk-...
BOT_SECRET=your_secret_here
```

### Run with Docker

```bash
docker compose up -d --build
```

API will be available at `http://localhost:8000`.  
Swagger docs: `http://localhost:8000/docs`

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn main:app --reload
```

### Run tests

```bash
pytest tests/ -v
```

## Database Schema

```
users              — Telegram users, moderators, nicknames
toilets            — Toilet locations with address and coordinates
reviews            — User reviews (one per user per toilet, soft delete)
moderator_reviews  — Official moderator reviews
toilet_of_month    — Monthly winner archive with AI comments
```

## Key Business Rules

- One user = one review per toilet (no editing)
- Moderators are assigned via bot by existing moderators
- Nicknames are unique and assigned by moderators only
- Deleted reviews are soft-deleted (hidden but kept in DB)
- Toilet of the month is picked automatically from highest avg score for the period
- AI comments are generated via GPT-4o on demand
