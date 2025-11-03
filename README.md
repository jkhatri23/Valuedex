# 🎴 Pokedictor - Pokemon Card Value Predictor

A modern web application that predicts Pokemon card values using machine learning and historical market data.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Next.js](https://img.shields.io/badge/next.js-14-black)
![License](https://img.shields.io/badge/license-MIT-purple)

## 🌟 Features

- 🔍 **Smart Card Search**: Search and select any English Pokemon card with autocomplete
- 📊 **Price Analytics**: View current stats, trends, and historical price data
- 🤖 **ML Predictions**: Predict card values 1-5 years into the future using hybrid AI models
- 💎 **Investment Rating**: Stock-style ratings (Strong Buy, Buy, Hold, Sell) with 1-10 scores
- 📈 **Interactive Charts**: Visualize price history and prediction timelines with Recharts
- 🎨 **Modern UI**: Beautiful, responsive design with Tailwind CSS and smooth animations
- 🔗 **External Links**: Direct links to TCGPlayer and eBay for purchasing
- 📱 **Responsive**: Works perfectly on desktop, tablet, and mobile devices

## 🚀 Quick Start

### Option 1: Using Helper Scripts (Easiest)

**Backend:**
```bash
cd backend
./run.sh
```

**Frontend (in a new terminal):**
```bash
cd frontend
./run.sh
```

Visit **http://localhost:3000** and you're done! 🎉

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Note:** No API key needed to start! The app includes mock data for testing.

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[SETUP.md](SETUP.md)** - Detailed local development guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment instructions

## 🏗️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Lucide React** - Beautiful icons

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **PostgreSQL/SQLite** - Database
- **Pandas & NumPy** - Data processing
- **Scikit-learn** - Machine learning
- **Prophet** - Time-series forecasting (hybrid model)

### Infrastructure
- **Vercel** - Frontend hosting
- **Google Cloud Run** - Backend hosting
- **Supabase** - PostgreSQL database
- **PriceCharting API** - Market data

## 🎯 How It Works

### Price Prediction Model

Pokedictor uses a **hybrid ML approach**:

1. **Time-Series Analysis**: Linear regression on historical price data to capture market trends
2. **Feature-Based Prediction**: Random Forest considering:
   - Card rarity (Common → Secret Rare)
   - Pokemon popularity (based on TCG/anime popularity)
   - Artist reputation (recognizes famous Pokemon artists)
   - Current market trends (30d, 90d, 1yr changes)
   - Price volatility

3. **Hybrid Combination**: Weighted average (60% time-series, 40% features) for final prediction

### Investment Rating System

Similar to stock ratings, cards receive a **1-10 score** based on:
- Growth potential
- Market stability
- Rarity and popularity
- Historical performance

Translated to: **Strong Buy** (8.5+), **Buy** (7+), **Hold** (5.5+), **Underperform** (4+), **Sell** (<4)

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cards/search?q={query}` | Search for cards |
| GET | `/api/cards/{card_id}` | Get card details |
| GET | `/api/cards/{card_id}/prices` | Get price history |
| GET | `/api/cards/{card_id}/rating` | Get investment rating |
| POST | `/api/predict` | Generate price prediction |

**Interactive Docs**: http://localhost:8000/docs

## 🗂️ Project Structure

```
pokedict/
├── frontend/                # Next.js application
│   ├── src/
│   │   ├── app/            # Pages and layouts
│   │   │   ├── page.tsx    # Main app page
│   │   │   └── layout.tsx  # Root layout
│   │   ├── components/      # React components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── CardDisplay.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── PredictionPanel.tsx
│   │   │   └── InvestmentRating.tsx
│   │   └── lib/
│   │       └── api.ts       # API client
│   ├── package.json
│   └── run.sh              # Quick start script
│
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── api/            # Route handlers
│   │   │   ├── cards.py    # Card endpoints
│   │   │   └── predictions.py
│   │   ├── ml/             # Machine learning
│   │   │   └── predictor.py
│   │   ├── models/         # Database models
│   │   │   └── card.py
│   │   ├── services/       # Business logic
│   │   │   ├── pricecharting.py
│   │   │   └── features.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.sh              # Quick start script
│
├── README.md               # This file
├── QUICKSTART.md           # 5-minute setup
├── SETUP.md                # Detailed setup guide
└── DEPLOYMENT.md           # Deployment instructions
```

## 🔑 Getting a PriceCharting API Key (Optional)

1. Visit https://www.pricecharting.com/api-documentation
2. Sign up for a free account
3. Get your API key
4. Add to `backend/.env`:
```env
PRICECHARTING_API_KEY=your_key_here
```

Without an API key, the app uses realistic mock data.

## 🚢 Deployment

### Frontend (Vercel)
```bash
# Push to GitHub
git init && git add . && git commit -m "Initial commit"
git remote add origin YOUR_REPO_URL
git push -u origin main

# Deploy on Vercel
# 1. Import repository
# 2. Set root directory to "frontend"
# 3. Add env: NEXT_PUBLIC_API_URL=your_api_url
# 4. Deploy!
```

### Backend (Google Cloud Run)
```bash
cd backend
gcloud run deploy pokedictor-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🎨 Screenshots

*Main search interface with modern gradient design*
*Card details with investment rating and price history*
*AI-powered prediction panel with confidence intervals*

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add user authentication and saved cards
- [ ] Implement card portfolio tracking
- [ ] Add more ML model options (LSTM, Prophet tuning)
- [ ] Real-time price alerts
- [ ] Card comparison tool
- [ ] Mobile app (React Native)

## ⚠️ Disclaimer

This application is for **entertainment and educational purposes only**. Price predictions are estimates based on historical data and should not be considered financial advice. Always do your own research before making investment decisions.

## 📄 License

MIT License - feel free to use this project for learning or building your own card value predictor!

## 🙏 Acknowledgments

- **PriceCharting** for market data API
- **Pokemon TCG** for card images
- **FastAPI** and **Next.js** communities

## 📞 Support

Having issues? Check out:
- [SETUP.md](SETUP.md) for troubleshooting
- [GitHub Issues](https://github.com/yourusername/pokedictor/issues)
- API Docs: http://localhost:8000/docs

---

Built with ❤️ for Pokemon card collectors and investors
