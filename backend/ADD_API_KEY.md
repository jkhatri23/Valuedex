# How to Add Your eBay API Keys

The app now uses **eBay's Browse API** for real-time Pokemon card prices and data, including grade-specific pricing (PSA 10, PSA 9, etc.).

## Step 1: Get Your eBay API Credentials

1. Visit: **https://developer.ebay.com/**
2. Sign in or create a developer account
3. Go to **My Account** → **Application Access Keys**
4. Create a new application (Production environment for real data)
5. You'll need three credentials:
   - **App ID** (Client ID)
   - **Dev ID** 
   - **Cert ID** (Client Secret)

## Step 2: Add API Keys to Your App

### Option A: Using .env file (Recommended)

Create or edit `backend/.env`:

```env
DATABASE_URL=sqlite:///./pokedict.db
PRICE_DATABASE_URL=sqlite:///./pricepoints.db
DEBUG=True

# eBay API Credentials (Browse API)
EBAY_APP_ID=your-app-id-here
EBAY_DEV_ID=your-dev-id-here
EBAY_CERT_ID=your-cert-id-here
```

### Option B: Using Terminal

```bash
cd backend
cat >> .env << EOF
EBAY_APP_ID=your-app-id-here
EBAY_DEV_ID=your-dev-id-here
EBAY_CERT_ID=your-cert-id-here
EOF
```

## Step 3: Restart the Backend

The backend auto-reloads, so it should pick up the new API keys automatically!

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
2. Check your backend terminal - you should see successful API calls
3. Results will include `"source": "ebay"` when working correctly

## API Features

With eBay API configured, you get:

✅ **Real-time prices** from actual eBay listings  
✅ **Grade-specific pricing** (PSA 10, PSA 9, PSA 8, etc.)  
✅ **Rarity detection** from listings  
✅ **Market average prices** (trimmed mean)  
✅ **Historical sold data** for trends  

## New Endpoints

### Search with Grades
```
GET /api/cards/search?q=charizard&include_grades=true
```
Returns cards with `prices_by_grade` showing prices for each PSA grade.

### Get Prices by Grade
```
GET /api/cards/{card_id}/grades?card_name=Charizard&set_name=Base+Set
```
Returns detailed pricing for each grade level.

## Example Response with Grades

```json
{
  "cards": [{
    "id": "abc123",
    "name": "Charizard",
    "set_name": "Base Set",
    "current_price": 250.00,
    "rarity": "Holo Rare",
    "prices_by_grade": {
      "PSA 10": {"average_price": 15000.00, "count": 5},
      "PSA 9": {"average_price": 2500.00, "count": 12},
      "PSA 8": {"average_price": 800.00, "count": 8},
      "Ungraded": {"average_price": 250.00, "count": 20}
    }
  }],
  "source": "ebay"
}
```

## Troubleshooting

### "eBay service not enabled"
- Check `.env` file exists in `backend/` folder
- Verify `EBAY_APP_ID` and `EBAY_CERT_ID` are set
- Make sure there are no spaces around the `=` sign

### "Failed to obtain OAuth token"
- Verify your Cert ID (Client Secret) is correct
- Check that your eBay app has the correct OAuth scope
- Ensure you're using Production keys (not Sandbox) for real data

### Empty results?
- eBay's Browse API may have rate limits
- Try broader search terms
- Check the backend logs for specific errors

## Legacy: PriceCharting API (Optional)

If you prefer to use PriceCharting instead:

```env
PRICECHARTING_API_KEY=your-key-here
```

Note: The app now defaults to eBay for real-time market data with grade support.

