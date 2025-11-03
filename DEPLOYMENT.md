# Deployment Guide

## Prerequisites

- Google Cloud Platform account with billing enabled
- Vercel account
- Supabase account (or other PostgreSQL provider)

## Backend Deployment (Google Cloud Run)

### 1. Setup GCP Project

```bash
# Install Google Cloud SDK if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login

# Create a new project or use existing
gcloud projects create pokedictor --name="Pokedictor"

# Set the project
gcloud config set project pokedictor

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Setup Database

Option A: Supabase (Recommended)
1. Go to https://supabase.com
2. Create a new project
3. Get the PostgreSQL connection string from Settings > Database
4. Format: `postgresql://postgres:[password]@[host]:[port]/postgres`

Option B: Cloud SQL
```bash
gcloud sql instances create pokedictor-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

### 3. Set Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://user:password@host:port/database
PRICECHARTING_API_KEY=your_api_key_here
DEBUG=False
```

### 4. Deploy to Cloud Run

```bash
cd backend

# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or use Docker directly
gcloud run deploy pokedictor-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,PRICECHARTING_API_KEY=$PRICECHARTING_API_KEY
```

### 5. Get the API URL

```bash
gcloud run services describe pokedictor-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

Save this URL for frontend configuration.

## Frontend Deployment (Vercel)

### 1. Push to GitHub

```bash
# Initialize git repository if not already done
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub
# Then push
git remote add origin https://github.com/yourusername/pokedictor.git
git branch -M main
git push -u origin main
```

### 2. Deploy to Vercel

1. Go to https://vercel.com
2. Click "Import Project"
3. Import your GitHub repository
4. Set the root directory to `frontend`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your Cloud Run API URL
6. Click "Deploy"

### 3. Configure Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed

## Database Migration

### Run Initial Migration

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# The tables will be created automatically when the app starts
# Or run Python to create them manually:
python -c "from app.database import engine, Base; from app.models.card import *; Base.metadata.create_all(bind=engine)"
```

## Monitoring and Logs

### View Cloud Run Logs

```bash
gcloud run services logs read pokedictor-api \
  --region us-central1 \
  --limit 50
```

### View Vercel Logs

Visit: https://vercel.com/dashboard/deployments

## Updating the Application

### Backend Updates

```bash
cd backend
gcloud builds submit --config cloudbuild.yaml
```

### Frontend Updates

Simply push to your GitHub repository - Vercel will automatically deploy:

```bash
git add .
git commit -m "Update frontend"
git push origin main
```

## Cost Optimization

### Google Cloud Run
- Free tier: 2 million requests per month
- Scales to zero when not in use
- Only pay for actual usage

### Vercel
- Free tier includes:
  - Unlimited deployments
  - 100 GB bandwidth per month
  - Automatic HTTPS

### Supabase
- Free tier includes:
  - 500 MB database
  - 2 GB bandwidth per month
  - Unlimited API requests

## Troubleshooting

### Backend not connecting to database

1. Check DATABASE_URL environment variable
2. Verify database is accessible from Cloud Run
3. Check Cloud Run logs for connection errors

### Frontend can't reach backend

1. Verify NEXT_PUBLIC_API_URL is set correctly
2. Check CORS settings in backend (app/main.py)
3. Ensure Cloud Run service allows unauthenticated requests

### API Key Issues

1. Verify PRICECHARTING_API_KEY is set
2. The app includes mock data if API key is not set
3. Check API rate limits if getting errors

## Security Notes

- Never commit `.env` files to version control
- Use environment variables for all secrets
- Enable Cloud Run authentication for production
- Consider adding rate limiting
- Use HTTPS only (automatic with Cloud Run and Vercel)

