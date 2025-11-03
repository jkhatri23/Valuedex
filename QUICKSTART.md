# Quick Start Guide

Get Pokedictor running in 5 minutes! 🚀

## Step 1: Clone or Navigate to Project

```bash
cd /Users/joeylu/Documents/development/pokedict
```

## Step 2: Start the Backend

Open a terminal:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

✅ Backend running at http://localhost:8000

## Step 3: Start the Frontend

Open a NEW terminal:

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend running at http://localhost:3000

## Step 4: Use the App

1. Open http://localhost:3000
2. Search for "Charizard"
3. Click on a card
4. Click "Generate Prediction"
5. View investment rating and price predictions!

## That's it! 🎉

The app uses mock data by default, so no API key needed to test.

### Want Real Data?

Get a free API key from https://www.pricecharting.com/api-documentation

Then create `backend/.env`:
```env
PRICECHARTING_API_KEY=your_key_here
```

Restart the backend and you're done!

