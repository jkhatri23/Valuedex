# Database Sync Guide

This guide explains how to populate and maintain your PostgreSQL database with Pokemon cards from pokemontcg.io.

## Overview

The system uses pokemontcg.io API to:
1. **Populate** the database with all Pokemon cards (one-time initial setup)
2. **Update** the database daily with new cards and price changes

## Initial Setup

### 1. Configure PostgreSQL Database

Make sure your `.env` file has the PostgreSQL connection string:

```env
DATABASE_URL=postgresql://user:password@host:port/database
PRICECHARTING_API_KEY=your_pokemontcg_api_key_here
```

**Note:** Get your API key from [pokemontcg.io](https://pokemontcg.io/).

### 2. Populate Database (First Time)

Run the population script to fetch ALL cards from pokemontcg.io:

```bash
cd backend
python scripts/populate_database.py
```

This will:
- Fetch all cards from pokemontcg.io API
- Save them to your PostgreSQL database
- Extract prices from TCGPlayer and Cardmarket
- Take approximately 10-30 minutes depending on your connection

**Example output:**
```
✅ Database population successful!
Total cards: 15,000+
New cards saved: 15,000+
Time: 1200.00 seconds
```

## Daily Updates

### Automatic Updates

The system automatically updates the database **daily at 2 AM UTC** using APScheduler.

To change the update time, edit `backend/app/main.py`:

```python
scheduler.add_job(
    daily_update_job,
    trigger=CronTrigger(hour=2, minute=0),  # Change hour here
    ...
)
```

### Manual Updates

You can trigger a manual update in two ways:

#### Option 1: API Endpoint

```bash
curl -X POST http://localhost:8000/api/admin/update-database
```

#### Option 2: Command Line

```bash
cd backend
python scripts/update_database.py
```

## API Endpoints

### Admin Endpoints

- `POST /api/admin/populate-database` - Trigger initial population (background task)
- `POST /api/admin/update-database` - Trigger manual update (background task)
- `GET /api/admin/sync-status` - Get database sync status

### Check Sync Status

```bash
curl http://localhost:8000/api/admin/sync-status
```

Response:
```json
{
  "success": true,
  "total_cards": 15234,
  "last_update": "2024-01-15T10:30:00",
  "scheduler_running": true
}
```

## How It Works

### Price Extraction

The system extracts prices from multiple sources in priority order:
1. **TCGPlayer** (US market) - market price or mid price
2. **Cardmarket** (European market) - average sell price or trend price
3. Falls back to $0.00 if no price available

### Database Updates

- **New cards**: Automatically saved when found
- **Existing cards**: Updated with latest information
- **Prices**: Added as new price history entries (one per day)
- **Images**: Updated if new image URL is available

### Performance

- **Search speed**: Instant (<100ms) for cards in database
- **Population**: ~10-30 minutes for all cards
- **Daily update**: ~5-10 minutes (only updates changed cards)

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM cards;"
```

### API Key Issues

Make sure your API key is set in `.env`:
```env
PRICECHARTING_API_KEY=your_key_here
```

### Rate Limiting

The sync service includes rate limiting (500ms delay between requests). If you encounter rate limits:
- Wait a few minutes and try again
- Consider using a paid API key for higher limits

### Check Logs

Monitor the application logs:
```bash
# When running the server
uvicorn app.main:app --reload

# Look for sync messages:
[SYNC] Starting database population...
[SYNC] Fetched 250 cards from page 1...
```

## Production Deployment

### Using Cron (Alternative to APScheduler)

If APScheduler doesn't work in your deployment environment, use system cron:

```bash
# Edit crontab
crontab -e

# Add daily update at 2 AM UTC
0 2 * * * cd /path/to/backend && python scripts/update_database.py >> /var/log/pokedict_update.log 2>&1
```

### Cloud Run / Serverless

For serverless deployments, you may need to:
1. Use Cloud Scheduler or similar to trigger updates
2. Create a separate Cloud Function for the update job
3. Call the API endpoint via HTTP request

## Next Steps

After populating the database:
1. ✅ Search is now instant for all cards in database
2. ✅ Prices are updated daily automatically
3. ✅ New cards are added automatically
4. ✅ No more waiting for external API calls!

