# Local Development Setup

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn
- PostgreSQL (optional - SQLite will be used by default)

## Backend Setup

### 1. Navigate to backend directory

```bash
cd backend
```

### 2. Create and activate virtual environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

Create a `.env` file in the backend directory (or just use defaults):

```env
DATABASE_URL=sqlite:///./pokedict.db
PRICECHARTING_API_KEY=
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

**Note:** The app works without a PriceCharting API key using mock data. To get a real API key:
1. Visit https://www.pricecharting.com/api-documentation
2. Sign up for an API key
3. Add it to your `.env` file

### 5. Run the backend

```bash
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## Frontend Setup

### 1. Navigate to frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Setup environment variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run the development server

```bash
npm run dev
```

The app will be available at: http://localhost:3000

## Testing the Application

1. Open http://localhost:3000 in your browser
2. Search for a Pokemon card (try "Charizard" or "Pikachu")
3. Click on a card to view details
4. Generate price predictions
5. View investment ratings and charts

## Project Structure

```
pokedict/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   │   ├── cards.py
│   │   │   └── predictions.py
│   │   ├── ml/           # Machine learning models
│   │   │   └── predictor.py
│   │   ├── models/       # Database models
│   │   │   └── card.py
│   │   ├── services/     # Business logic
│   │   │   ├── pricecharting.py
│   │   │   └── features.py
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   │   ├── page.tsx
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/   # React components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── CardDisplay.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── PredictionPanel.tsx
│   │   │   └── InvestmentRating.tsx
│   │   └── lib/          # Utilities
│   │       └── api.ts
│   ├── package.json
│   └── tailwind.config.ts
└── README.md
```

## Common Issues

### Backend won't start

**Issue:** Module not found errors
**Solution:** Make sure you're in the virtual environment and all dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Issue:** Database connection errors
**Solution:** Use SQLite by default (no setup required) or ensure PostgreSQL is running

### Frontend won't start

**Issue:** Module not found
**Solution:** Install dependencies:
```bash
npm install
```

**Issue:** Can't connect to API
**Solution:** Ensure backend is running on port 8000 and NEXT_PUBLIC_API_URL is set correctly

### CORS errors

**Issue:** Browser blocks API requests
**Solution:** The backend is configured to allow localhost:3000. If using different ports, update `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your port
    ...
)
```

## Development Tips

1. **Hot Reload:** Both frontend and backend support hot reload. Changes will be reflected automatically.

2. **Database Reset:** To reset the database:
   ```bash
   cd backend
   rm pokedict.db  # Remove SQLite database
   # Restart the backend - it will create a fresh database
   ```

3. **API Testing:** Use the interactive API docs at http://localhost:8000/docs

4. **Mock Data:** The app includes mock data for testing without API keys. Real API integration works seamlessly when you add a key.

5. **Styling:** Tailwind CSS classes can be modified in components. The design system is in `frontend/src/app/globals.css`

## Next Steps

- [ ] Add your PriceCharting API key for real data
- [ ] Customize the ML model parameters in `backend/app/ml/predictor.py`
- [ ] Add more card features and metrics
- [ ] Implement user authentication
- [ ] Add favorite cards feature
- [ ] Create a comparison tool for multiple cards

## Getting Help

- Backend API Docs: http://localhost:8000/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- Next.js Docs: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs

Enjoy building with Pokedictor! 🎴✨

