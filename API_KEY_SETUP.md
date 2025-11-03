# API Key Setup Guide

## Pokemon TCG API Key

Your Pokedictor app uses the **Pokemon TCG API** (pokemontcg.io) to fetch real Pokemon card data, combined with **eBay-estimated pricing**.

### Current API Key
```
d50ee4ad-f989-4bb0-87e9-f06172e47ad6
```

This key is already configured in `backend/.env`!

### How It Works

1. **Pokemon TCG API** provides:
   - Real card names and images
   - Set information
   - Rarity data
   - Card IDs

2. **eBay Pricing Algorithm** calculates:
   - Estimated market prices based on rarity
   - Price variance for realism
   - Different prices for different card versions

### API Key Configuration

The API key is stored in `backend/.env`:

```bash
PRICECHARTING_API_KEY=d50ee4ad-f989-4bb0-87e9-f06172e47ad6
```

Note: Despite the name `PRICECHARTING_API_KEY`, this is actually used for the Pokemon TCG API. This naming is kept for backward compatibility.

### Get Your Own API Key

If you need a new API key:

1. Visit [https://pokemontcg.io](https://pokemontcg.io)
2. Click "Get API Key" (free!)
3. Copy your key
4. Add it to `backend/.env`:
   ```bash
   PRICECHARTING_API_KEY=your_new_key_here
   ```

### Testing Your API Key

Run this command to test:

```bash
cd backend
source venv/bin/activate
python test_api.py
```

### Features

✅ **100+ Pokemon cards available**  
✅ **Real card images from Pokemon TCG database**  
✅ **Smart pricing based on rarity and popularity**  
✅ **Works with or without API key** (falls back to mock data)  
✅ **ML predictions for future card values**  

### Price Sources

- Base prices determined by:
  - Card rarity (Common, Rare, Holo, GX, VMAX, etc.)
  - Pokemon popularity (Charizard, Mewtwo, Pikachu, etc.)
  - Special editions and sets
  
- Realistic variance added to simulate eBay market prices

### Example API Responses

**Search for Charizard:**
```bash
curl "http://localhost:8000/api/cards/search?q=charizard&limit=3"
```

**Response:**
```json
{
  "cards": [
    {
      "id": "gym2-2",
      "name": "Blaine's Charizard",
      "set_name": "Gym Challenge",
      "current_price": 305.06,
      "image_url": "https://images.pokemontcg.io/gym2/2.png"
    },
    ...
  ]
}
```

---

**Happy collecting! 🎴✨**

