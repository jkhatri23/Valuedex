#!/bin/bash

# Script to run the backend server

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Pokedictor Backend...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run the server
echo -e "${GREEN}✓ Backend starting on http://localhost:8000${NC}"
echo -e "${GREEN}✓ API docs available at http://localhost:8000/docs${NC}"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

