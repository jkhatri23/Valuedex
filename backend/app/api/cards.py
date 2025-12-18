from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from statistics import median
import math
from urllib.parse import quote_plus
import random
import asyncio

from app.database import get_db, SessionLocal
from app.models.card import Card, PriceHistory, CardFeature
from app.models.price_point import PricePoint as PricePointModel
from app.price_database import get_price_db
from app.services.pricecharting import pricecharting_service
from app.services.features import feature_service
from pydantic import BaseModel

router = APIRouter()

# Pydantic schemas
class CardSearchResult(BaseModel):
    id: str
    name: str
    set_name: str
    current_price: float
    image_url: Optional[str] = None

class CardDetail(BaseModel):
    id: int
    external_id: str
    name: str
    set_name: str
    rarity: Optional[str]
    artist: Optional[str]
    release_year: Optional[int]
    card_number: Optional[str]
    image_url: Optional[str]
    tcgplayer_url: Optional[str]
    ebay_url: Optional[str]
    current_price: float
    features: Optional[dict] = None

class PricePoint(BaseModel):
    date: str
    price: float
    volume: Optional[int] = None
    grade: Optional[str] = None


def _aggregate_price_points(
    points: List[Dict],
    max_points: int = 180,
) -> List[Dict]:
    """
    Downsample price points to monthly medians to keep trend shape while
    reducing noisy/high-volume data.
    """
    if not points:
        return []

    parsed: List[Tuple[datetime, Dict]] = []
    for point in points:
        date_str = point.get("date")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            continue
        parsed.append((dt, point))

    if not parsed:
        return []

    parsed.sort(key=lambda x: x[0])

    # If already under the limit, just normalize date formatting.
    if len(parsed) <= max_points:
        return [{**p, "date": dt.isoformat()} for dt, p in parsed]

    buckets: Dict[str, List[Dict]] = {}
    for dt, point in parsed:
        key = f"{dt.year:04d}-{dt.month:02d}"
        buckets.setdefault(key, []).append({**point, "date": dt})

    aggregated: List[Dict] = []
    for key in sorted(buckets.keys()):
        entries = buckets[key]
        prices = [e.get("price") for e in entries if e.get("price") is not None]
        if not prices:
            continue
        volumes = [e.get("volume") for e in entries if e.get("volume") is not None]
        median_price = round(median(prices), 2)
        avg_volume = int(sum(volumes) / len(volumes)) if volumes else None

        representative_dt = (
            entries[-1]["date"]
            if isinstance(entries[-1]["date"], datetime)
            else parsed[0][0]
        )

        aggregated.append(
            {
                "date": representative_dt.isoformat(),
                "price": median_price,
                "volume": avg_volume,
                "grade": entries[0].get("grade"),
                "source": entries[0].get("source") or "aggregated",
            }
        )

    aggregated.sort(key=lambda x: x["date"])

    # Further downsample if needed while preserving endpoints.
    if len(aggregated) > max_points:
        step = math.ceil(len(aggregated) / max_points)
        aggregated = aggregated[::step]

    # Ensure first and last real observations are kept for accuracy.
    first_dt, first_point = parsed[0]
    last_dt, last_point = parsed[-1]

    if not aggregated or aggregated[0]["date"] != first_dt.isoformat():
        aggregated.insert(0, {**first_point, "date": first_dt.isoformat()})
    if aggregated[-1]["date"] != last_dt.isoformat():
        aggregated.append({**last_point, "date": last_dt.isoformat()})

    return aggregated

@router.get("/search")
async def search_cards(
    q: str, 
    limit: int = 20, 
    set_name: Optional[str] = None,
    rarity: Optional[str] = None,
    db: Session = Depends(get_db), 
    background_tasks: BackgroundTasks = None
):
    """Search for Pokemon cards - instant results from local database, with optional background API enrichment.
    
    Supports:
    - General search: searches both card name and set name
    - Set-specific search: use 'set_name' parameter or 'set:<name>' in query
    - Rarity filter: use 'rarity' parameter
    - Multi-word queries: "charizard base set" will match cards named "charizard" from "Base Set"
    
    Examples:
    - /search?q=charizard - searches for "charizard" in name or set
    - /search?q=charizard&set_name=Base Set - searches for "charizard" specifically in "Base Set"
    - /search?q=set:Base Set - searches for cards from "Base Set"
    - /search?q=pikachu&rarity=Holo - searches for "pikachu" with Holo rarity
    """
    
    # Step 1: Search local database first for INSTANT results
    query_clean = q.strip()
    
    # Parse query for special syntax like "set:Base Set" or "name:Charizard"
    name_query = None
    set_query = None
    
    if query_clean.startswith("set:"):
        # Extract set name from "set:Base Set" syntax
        set_query = query_clean[4:].strip()
        query_clean = ""  # Clear name query
    elif query_clean.startswith("name:"):
        # Extract card name from "name:Charizard" syntax
        name_query = query_clean[5:].strip()
        query_clean = ""  # Clear general query
    elif " in " in query_clean.lower() or " from " in query_clean.lower():
        # Try to parse "charizard in base set" or "charizard from base set"
        parts = query_clean.lower().split(" in ")
        if len(parts) == 2:
            name_query = parts[0].strip()
            set_query = parts[1].strip()
            query_clean = ""  # Clear general query
        else:
            parts = query_clean.lower().split(" from ")
            if len(parts) == 2:
                name_query = parts[0].strip()
                set_query = parts[1].strip()
                query_clean = ""  # Clear general query
    
    # Use provided parameters if available, otherwise use parsed values
    if set_name:
        set_query = set_name
    if not name_query and query_clean:
        name_query = query_clean
    
    # Build search query with filters
    db_query = db.query(Card).join(CardFeature, Card.id == CardFeature.card_id, isouter=True)
    
    # Build filter conditions
    filters = []
    
    if name_query:
        # Search in card name
        name_pattern = f"%{name_query}%"
        filters.append(Card.name.like(name_pattern))
    
    if set_query:
        # Search in set name
        set_pattern = f"%{set_query}%"
        filters.append(Card.set_name.like(set_pattern))
    
    if not name_query and not set_query and query_clean:
        # General search - search both name and set if no specific syntax
        search_pattern = f"%{query_clean}%"
        filters.append(
            or_(
                Card.name.like(search_pattern),
                Card.set_name.like(search_pattern)
            )
        )
    
    if rarity:
        # Filter by rarity
        filters.append(Card.rarity.like(f"%{rarity}%"))
    
    if filters:
        db_query = db_query.filter(*filters)
    
    db_query = db_query.limit(limit)
    db_cards = db_query.all()
    
    # Format database results
    cards = []
    for card in db_cards:
        # Get current price from features if available, otherwise use latest price history
        current_price = 0
        if card.features:
            current_price = card.features.current_price or 0
        else:
            # Try to get from latest price history
            latest_price = db.query(PriceHistory).filter(
                PriceHistory.card_id == card.id
            ).order_by(PriceHistory.date.desc()).first()
            if latest_price:
                current_price = latest_price.price_loose or 0
        
        cards.append({
            "id": card.external_id or str(card.id),
            "name": card.name,
            "set_name": card.set_name or "Unknown Set",
            "current_price": current_price,
            "image_url": card.image_url
        })
    
    # If we have results from database, return them instantly
    if cards:
        # Optionally fetch from external API in background to enrich results
        # This doesn't block the response, so users get instant results
        if background_tasks and len(cards) < limit:
            background_tasks.add_task(_enrich_search_results, q, limit)
        
        return {"cards": cards, "count": len(cards), "source": "database"}
    
    # Step 2: If no local results, try external API (but with shorter timeout)
    # This is a fallback for cards not yet in the database
    try:
        # Use a shorter timeout for external API
        external_results = await asyncio.wait_for(
            asyncio.to_thread(pricecharting_service.search_cards, q, limit),
            timeout=5.0  # 5 second timeout instead of 60
        )
        
        external_cards = []
        for item in external_results:
            external_cards.append({
                "id": item.get("id"),
                "name": item.get("product-name"),
                "set_name": item.get("console-name", "Unknown Set"),
                "current_price": item.get("loose-price", 0),
                "image_url": item.get("image")
            })
        
        # Save new cards to database in background for faster future searches
        if background_tasks:
            background_tasks.add_task(_save_cards_to_db, external_results)
        
        return {"cards": external_cards, "count": len(external_cards), "source": "external"}
    except asyncio.TimeoutError:
        # If external API times out, return empty results
        return {"cards": [], "count": 0, "source": "timeout"}
    except Exception as e:
        print(f"[SEARCH] Error fetching from external API: {e}")
        return {"cards": [], "count": 0, "source": "error"}


def _enrich_search_results(query: str, limit: int):
    """Background task to enrich search results from external API"""
    try:
        external_results = pricecharting_service.search_cards(query, limit)
        _save_cards_to_db(external_results)
    except Exception as e:
        print(f"[BACKGROUND] Error enriching search results: {e}")


def _save_cards_to_db(external_results: List[Dict]):
    """Save external API results to database for faster future searches.
    Only saves cards that don't already exist in the database (checked by external_id).
    """
    db = SessionLocal()
    saved_count = 0
    skipped_count = 0
    try:
        for item in external_results:
            external_id = item.get("id")
            if not external_id:
                skipped_count += 1
                continue
            
            # Check if card already exists
            existing_card = db.query(Card).filter(Card.external_id == external_id).first()
            if existing_card:
                skipped_count += 1
                continue  # Already in database - skip duplicate
            
            # Create new card (only if it doesn't exist)
            card = Card(
                external_id=external_id,
                name=item.get("product-name", ""),
                set_name=item.get("console-name", "Unknown"),
                image_url=item.get("image")
            )
            db.add(card)
            db.flush()  # Flush to get the card.id
            
            # Create initial price history entry (real price from API, no simulation)
            # Historical data will be built over time by daily updates
            price = item.get("loose-price", 0)
            if price > 0:
                price_record = PriceHistory(
                    card_id=card.id,
                    date=datetime.now(),
                    price_loose=price,
                    volume=0,
                    source="external_api"
                )
                db.add(price_record)
            
            saved_count += 1
        
        db.commit()
        print(f"[BACKGROUND] Processed {len(external_results)} cards: {saved_count} saved, {skipped_count} skipped (already in DB)")
    except Exception as e:
        print(f"[BACKGROUND] Error saving cards to DB: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/{card_id}")
async def get_card_detail(card_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a card"""
    
    # Check if card exists in DB
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        # Fetch from API and create
        card_data = pricecharting_service.get_card_by_id(card_id)
        
        if not card_data:
            # If we can't fetch the card details, return a minimal response
            # using data from the search result if available
            raise HTTPException(
                status_code=404, 
                detail=f"Card {card_id} not found. The Pokemon TCG API may be slow or unavailable."
            )
        
        # Create card - use real data from Pokemon TCG API
        release_year = None
        if card_data.get("set_release"):
            try:
                release_year = int(card_data["set_release"].split("/")[0])
            except:
                release_year = _extract_year(card_data.get("console-name", ""))
        
        tcgplayer_url = card_data.get("tcgplayer_url") or _build_tcgplayer_url(
            card_data.get("product-name"),
            card_data.get("console-name")
        )
        ebay_url = card_data.get("ebay_url") or _build_ebay_url(
            card_data.get("product-name"),
            card_data.get("console-name")
        )

        card = Card(
            external_id=card_id,
            name=card_data.get("product-name"),
            set_name=card_data.get("console-name", "Unknown"),
            rarity=card_data.get("rarity") or _extract_rarity(card_data.get("product-name", "")),
            artist=card_data.get("artist") or _get_random_artist(),
            release_year=release_year or _extract_year(card_data.get("console-name", "")),
            card_number=card_data.get("number"),
            image_url=card_data.get("image"),
            tcgplayer_url=tcgplayer_url,
            ebay_url=ebay_url
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        
        # Create initial price history (real price from API, no simulation)
        # Historical data will be built over time by daily updates
        current_price = card_data.get("loose-price", 0)
        if current_price > 0:
            price_record = PriceHistory(
                card_id=card.id,
                date=datetime.now(),
                price_loose=current_price,
                volume=0,
                source="pokemontcg_api"
            )
            db.add(price_record)
            db.commit()
        
        # Create features
        features_dict = feature_service.create_card_features(card, current_price, [])
        card_features = CardFeature(card_id=card.id, **features_dict)
        db.add(card_features)
        db.commit()
    
    # Get features
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    tcgplayer_url = card.tcgplayer_url or _build_tcgplayer_url(card.name, card.set_name)
    ebay_url = card.ebay_url or _build_ebay_url(card.name, card.set_name)

    return {
        "id": card.id,
        "external_id": card.external_id,
        "name": card.name,
        "set_name": card.set_name,
        "rarity": card.rarity,
        "artist": card.artist,
        "release_year": card.release_year,
        "card_number": card.card_number,
        "image_url": card.image_url,
        "tcgplayer_url": tcgplayer_url,
        "ebay_url": ebay_url,
        "current_price": features.current_price if features else 0,
        "features": {
            "popularity_score": features.popularity_score,
            "rarity_score": features.rarity_score,
            "artist_score": features.artist_score,
            "trend_30d": features.trend_30d,
            "trend_90d": features.trend_90d,
            "trend_1y": features.trend_1y,
            "volatility": features.price_volatility,
            "market_sentiment": features.market_sentiment,
            "investment_score": features.investment_score,
            "investment_rating": features.investment_rating
        } if features else None
    }

@router.get("/{card_id}/prices")
async def get_price_history(
    card_id: str,
    db: Session = Depends(get_db),
    price_db: Session = Depends(get_price_db),
    grade: Optional[str] = None,
):
    """
    Get price history for a card.

    - Without a grade: returns the traditional loose-price history from the main DB.
    - With a grade (e.g. 'Near Mint', 'PSA 9'): returns grade-specific prices from
      the price_points database, sorted chronologically.
    """

    card = db.query(Card).filter(Card.external_id == card_id).first()

    if not card:
        # Try to get card detail first (will create it)
        await get_card_detail(card_id, db)
        card = db.query(Card).filter(Card.external_id == card_id).first()

    if grade:
        # Grade-specific history from price_points DB only.
        # If there are no grade-specific rows, we return an empty array
        # rather than falling back to loose prices.
        
        # Map "Near Mint" to None (ungraded) for database query
        db_grade = None if grade == "Near Mint" else grade
        
        query = price_db.query(PricePointModel).filter(
            PricePointModel.card_external_id == card.external_id,
            PricePointModel.grade == db_grade,
        )
        points = query.order_by(PricePointModel.collected_at.asc()).all()

        price_points = [
            {
                "date": p.collected_at.isoformat(),
                "price": p.price or 0,
                "volume": p.volume,
                "grade": p.grade,
                "source": p.source,
            }
            for p in points
        ]
    else:
        # Default loose-price history from main DB
        prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.card_id == card.id)
            .order_by(PriceHistory.date.asc())
            .all()
        )

        price_points = [
            {
                "date": p.date.isoformat(),
                "price": p.price_loose or 0,
                "volume": p.volume,
                "grade": None,
            }
            for p in prices
        ]

    price_points = _aggregate_price_points(price_points)

    return {"card_id": card_id, "prices": price_points}

@router.get("/{card_id}/rating")
async def get_investment_rating(card_id: str, db: Session = Depends(get_db)):
    """Get investment rating for a card"""
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    if not features:
        raise HTTPException(status_code=404, detail="Features not calculated")
    
    return {
        "card_id": card_id,
        "investment_score": features.investment_score,
        "investment_rating": features.investment_rating,
        "current_price": features.current_price,
        "trends": {
            "30d": features.trend_30d,
            "90d": features.trend_90d,
            "1y": features.trend_1y
        },
        "factors": {
            "rarity_score": features.rarity_score,
            "popularity_score": features.popularity_score,
            "artist_score": features.artist_score,
            "volatility": features.price_volatility
        }
    }

def _aggregate_price_points(price_points: List[Dict], max_points: int = 180) -> List[Dict]:
    """
    Aggregate price points by month using median, keeping first/last points.
    Reduces data while preserving trend shape.
    """
    if not price_points or len(price_points) <= max_points:
        return price_points
    
    from collections import defaultdict
    from statistics import median
    from datetime import datetime
    
    # Group by year-month
    by_month = defaultdict(list)
    for point in price_points:
        dt = datetime.fromisoformat(point["date"].replace("Z", "+00:00"))
        month_key = (dt.year, dt.month)
        by_month[month_key].append(point)
    
    # Take median of each month
    aggregated = []
    for month_key in sorted(by_month.keys()):
        points_in_month = by_month[month_key]
        prices = [p["price"] for p in points_in_month if p["price"] > 0]
        
        if prices:
            median_price = median(prices)
            # Use the middle point's date
            mid_point = points_in_month[len(points_in_month) // 2]
            aggregated.append({
                "date": mid_point["date"],
                "price": round(median_price, 2),
                "volume": mid_point.get("volume"),
                "grade": mid_point.get("grade"),
                "source": mid_point.get("source"),
            })
    
    # Always keep first and last original points for accuracy
    if aggregated and price_points:
        aggregated[0] = price_points[0]
        aggregated[-1] = price_points[-1]
    
    return aggregated

# Helper functions
def _extract_rarity(name: str) -> str:
    """Extract rarity from card name"""
    name_lower = name.lower()
    if "holo" in name_lower or "holographic" in name_lower:
        return "Holo Rare"
    elif "ultra rare" in name_lower:
        return "Ultra Rare"
    elif "secret" in name_lower:
        return "Secret Rare"
    elif "rare" in name_lower:
        return "Rare"
    return "Uncommon"

def _get_random_artist() -> str:
    """Get a random Pokemon card artist"""
    artists = [
        "Ken Sugimori",
        "Mitsuhiro Arita",
        "Atsuko Nishida",
        "Kouki Saitou",
        "Sowsow",
        "5ban Graphics",
        "Kagemaru Himeno",
        "Yuka Morii"
    ]
    return random.choice(artists)

def _extract_year(set_name: str) -> int:
    """Extract or estimate release year"""
    if "base set" in set_name.lower():
        return 1999
    elif "fossil" in set_name.lower() or "jungle" in set_name.lower():
        return 2000
    return random.randint(2018, 2024)


def _build_tcgplayer_url(card_name: Optional[str], set_name: Optional[str] = None) -> str:
    """Create a TCGplayer search URL for the given card"""
    query_parts = [card_name or "", set_name or ""]
    query = " ".join(part for part in query_parts if part).strip() or "pokemon card"
    encoded = quote_plus(query)
    return f"https://www.tcgplayer.com/search/pokemon/product?q={encoded}&productLineName=pokemon"


def _build_ebay_url(card_name: Optional[str], set_name: Optional[str] = None) -> str:
    """Create an eBay search URL for the given card"""
    query_parts = [card_name or "", set_name or "", "pokemon card"]
    query = " ".join(part for part in query_parts if part).strip()
    encoded = quote_plus(query or "pokemon card")
    return f"https://www.ebay.com/sch/i.html?_nkw={encoded}"


