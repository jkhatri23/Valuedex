# 🚀 Quick Guide: Add Real Pokemon Card Data

## 3-Step Setup

### 1️⃣ Get Your Free API Key
Visit: **https://www.pricecharting.com/api-documentation**
- Click "Get API Key"
- Sign up (free!)
- Copy your API key

### 2️⃣ Add to Your App
Open `backend/.env` and add your key:
```bash
PRICECHARTING_API_KEY=your_actual_key_here
```

### 3️⃣ Test It!
```bash
cd backend
python test_api.py
```

**That's it!** The backend auto-reloads and you now have access to **thousands of real Pokemon cards**! 🎉

---

## What Changes?

| Before (Mock Data) | After (Real API) |
|-------------------|------------------|
| 10 cards only | Thousands of cards |
| Simulated prices | Real market prices |
| Generated trends | Actual price history |
| Limited sets | All Pokemon TCG sets |

## Verify It's Working

1. **Search in the app** - Try searching for "Lugia" or "Rayquaza"
2. **Check backend logs** - You should see:
   ```
   [API] Searching PriceCharting for: lugia
   [API] Found 25 cards from PriceCharting
   ```

## Without API Key

**No problem!** The app works perfectly with mock data. You get:
- ✅ Full app functionality
- ✅ AI predictions
- ✅ Investment ratings
- ✅ Charts and analytics
- ✅ 10 popular cards to test with

Add the API key whenever you're ready for real data!

## Troubleshooting

**Still seeing mock data?**
- Restart backend: `Ctrl+C` then run `uvicorn app.main:app --reload` again
- Check `.env` file is in `backend/` directory
- Run `python test_api.py` to diagnose

**API errors?**
- Verify API key is correct (no spaces or quotes)
- Check you haven't exceeded 1,000 calls/day
- Visit PriceCharting to verify account status

## Need Help?

📚 Read: `backend/ADD_API_KEY.md` for detailed instructions  
🧪 Run: `backend/test_api.py` to test your connection  
🌐 Visit: https://www.pricecharting.com/api-documentation for API docs

---

**Your app is ready to go at http://localhost:3000** 🎴✨

