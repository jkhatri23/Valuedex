# Pokedict

A Pokemon card value predictor that uses historical market data and ML to forecast card prices.

## Setup

### Backend

```bash
cd backend
./run.sh
```

API runs at http://localhost:8000 (docs at http://localhost:8000/docs).

### Frontend

In a separate terminal:

```bash
cd frontend
./run.sh
```

App runs at http://localhost:3000.

### Populating the database

Clone the Pokemon TCG data repo and run the bulk populate script:

```bash
git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git /tmp/pokemon-tcg-data
cd backend
python scripts/bulk_populate.py --max-cards 5000
```

## Tech stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Recharts
- **Backend:** FastAPI, SQLAlchemy, Pandas, scikit-learn
- **Database:** SQLite (dev) / PostgreSQL (prod)

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cards/search?q={query}` | Search cards |
| GET | `/api/cards/{card_id}` | Card details |
| GET | `/api/cards/{card_id}/prices` | Price history |
| GET | `/api/cards/{card_id}/rating` | Investment rating |
| POST | `/api/predict` | Price prediction |

## Deployment

- **Frontend:** Vercel (set root to `frontend`, add `NEXT_PUBLIC_API_URL` env var)
- **Backend:** Google Cloud Run via the included `Dockerfile` and `cloudbuild.yaml`
