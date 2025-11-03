# 🎴 How to Run Pokedictor on Your Laptop

A simple guide for anyone to run this Pokemon Card Value Predictor app!

## Prerequisites

You need to have these installed:
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Git** - [Download here](https://git-scm.com/downloads)

## Step 1: Get the Code

Open Terminal (Mac) or Command Prompt (Windows) and run:

```bash
git clone https://github.com/jkhatri23/Pokedict.git
cd Pokedict
```

✅ This downloads all the code to your computer!

## Step 2: Start the Backend (API Server)

### Mac/Linux:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "DATABASE_URL=sqlite:///./pokedict.db" > .env
echo "PRICECHARTING_API_KEY=" >> .env
uvicorn app.main:app --reload
```

### Windows:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
echo DATABASE_URL=sqlite:///./pokedict.db > .env
echo PRICECHARTING_API_KEY= >> .env
uvicorn app.main:app --reload
```

✅ Backend now running at http://localhost:8000

**Keep this terminal window open!**

## Step 3: Start the Frontend (Website)

Open a **NEW** terminal window and run:

```bash
cd Pokedict/frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

✅ Website now running at http://localhost:3000

**Keep this terminal window open too!**

## Step 4: Use the App!

Open your browser and go to: **http://localhost:3000**

Try it out:
1. Search for "Charizard" or "Pikachu"
2. Click on a card
3. View price history
4. Click "Generate Prediction"
5. Check the investment rating!

## Troubleshooting

### "Python not found"
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### "npm not found"
- Install Node.js from https://nodejs.org/
- Restart your terminal after installing

### "Port already in use"
- Close any other programs using ports 3000 or 8000
- Or change the port numbers in the commands

### Backend crashes
- Make sure you created the `.env` file
- Check Python version: `python --version` (should be 3.11+)

### Frontend errors
- Delete `node_modules` folder
- Run `npm install` again

## To Stop the App

Press `Ctrl+C` in both terminal windows

## To Run It Again Later

**Terminal 1 (Backend):**
```bash
cd Pokedict/backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd Pokedict/frontend
npm run dev
```

## Features

✅ Search thousands of Pokemon cards  
✅ View price history charts  
✅ AI price predictions (1-5 years)  
✅ Investment ratings (like stocks!)  
✅ External marketplace links  

## Optional: Add Real Card Data

The app works with mock data, but for real Pokemon card prices:

1. Get a free API key from https://www.pricecharting.com/api-documentation
2. Open `backend/.env` file
3. Add your key: `PRICECHARTING_API_KEY=your_key_here`
4. Restart the backend

Now you have access to thousands of real cards!

## Need Help?

Check these files:
- **README.md** - Main documentation
- **QUICKSTART.md** - Quick setup guide
- **SETUP.md** - Detailed setup

## System Requirements

- **OS**: Mac, Windows, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 500MB for app + dependencies
- **Internet**: Required for npm/pip downloads

---

That's it! Enjoy predicting Pokemon card values! 🎴✨

