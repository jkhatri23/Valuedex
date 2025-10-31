#!/usr/bin/env python3
"""
Test script to verify PriceCharting API connection
Run this to check if your API key is working!
"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

API_KEY = os.getenv('PRICECHARTING_API_KEY', '')

print("="*60)
print("🧪 PRICECHARTING API TEST")
print("="*60)

# Check if API key exists
if not API_KEY or not API_KEY.strip():
    print("\n❌ No API key found!")
    print("\n📝 To add your API key:")
    print("   1. Get key from: https://www.pricecharting.com/api-documentation")
    print("   2. Add to backend/.env file:")
    print("      PRICECHARTING_API_KEY=your_key_here")
    print("\n✅ Don't worry! The app works without an API key using mock data.")
    sys.exit(0)

print(f"\n✅ API Key found: {API_KEY[:10]}...")

# Test the API
print("\n🔍 Testing API connection...")
print("Searching for: Charizard")

try:
    url = "https://www.pricecharting.com/api/products"
    params = {
        "q": "charizard",
        "t": "pokemon-cards",
        "apikey": API_KEY
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if "products" in data:
        products = data["products"]
        print(f"\n✅ SUCCESS! Found {len(products)} cards")
        print("\n📊 Sample results:")
        for i, card in enumerate(products[:5], 1):
            name = card.get('product-name', 'Unknown')
            price = card.get('loose-price', 0)
            set_name = card.get('console-name', 'Unknown Set')
            print(f"   {i}. {name} - ${price} ({set_name})")
        
        print("\n" + "="*60)
        print("🎉 Your API key is working perfectly!")
        print("The app will now use real Pokemon card data!")
        print("="*60)
    else:
        print("\n⚠️  API returned unexpected format")
        print(f"Response: {data}")
        
except requests.exceptions.HTTPError as e:
    print(f"\n❌ HTTP Error: {e}")
    if e.response.status_code == 401:
        print("   Invalid API key - please check your key")
    elif e.response.status_code == 429:
        print("   Rate limit exceeded - try again later")
    else:
        print(f"   Status code: {e.response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Connection Error: {e}")
    print("   Check your internet connection")
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")

print()

