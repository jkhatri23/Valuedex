# How to Add Your PriceCharting API Key

## Step 1: Get Your API Key

1. Visit: **https://www.pricecharting.com/api-documentation**
2. Click **"Get API Key"** or **"Sign Up"**
3. Create a free account
4. Copy your API key (it will look like: `abc123def456...`)

## Step 2: Add API Key to Your App

### Option A: Using .env file (Recommended)

Open `backend/.env` and update the API key line:

```env
DATABASE_URL=sqlite:///./pokedict.db
PRICECHARTING_API_KEY=paste_your_api_key_here
DEBUG=True
```

### Option B: Using Terminal

```bash
cd backend
echo "PRICECHARTING_API_KEY=your_api_key_here" >> .env
```

## Step 3: Restart the Backend

The backend auto-reloads, so it should pick up the new API key automatically!

If not, restart it:

```bash
# Stop the current backend (Ctrl+C)
# Then restart:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## How to Test It Works

1. Search for any Pokemon card in the app
2. Check your backend terminal - you should see:
   ```
   [API] Searching PriceCharting for: charizard
   [API] Found 15 cards from PriceCharting
   ```

3. If you see `[INFO] No API key found - using mock data`, the key isn't set correctly

## API Key Features

With a real API key, you get:

✅ **Real-time prices** for ALL Pokemon cards
✅ **Thousands of cards** from all sets
✅ **Actual market data** from PriceCharting
✅ **Historical price trends**
✅ **1,000 requests/day** (free tier)

## Free vs Mock Data

| Feature | With API Key | Without API Key |
|---------|--------------|-----------------|
| Card Search | Real data from thousands of cards | 10 mock cards only |
| Prices | Live market prices | Simulated prices |
| Price History | Actual historical data | Generated trends |
| Card Coverage | All Pokemon TCG cards | Limited selection |

## Troubleshooting

### "No API key found"
- Check `.env` file exists in `backend/` folder
- Make sure there are no spaces around the `=` sign
- Make sure API key has no extra quotes

### "API error"
- Check your API key is valid
- Verify you haven't exceeded rate limits (1,000/day)
- Check PriceCharting service status

### Still using mock data?
- Restart the backend server
- Check terminal logs for error messages
- Verify `.env` file is in the correct location

## Without API Key

The app works great without an API key using realistic mock data!
This is perfect for:
- Testing the app
- Development
- Demonstrating features
- Learning how it works

You can always add the API key later when you're ready for real data!

