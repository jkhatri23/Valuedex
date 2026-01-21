"""Card API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from statistics import median
from urllib.parse import quote_plus
from collections import defaultdict
import random
import asyncio

from app.database import get_db, SessionLocal
from app.models.card import Card, PriceHistory, CardFeature
from app.models.price_point import PricePoint as PricePointModel
from app.price_database import get_price_db
from app.services.ebay import ebay_price_service
from app.services.pokemon_tcg import pokemon_tcg_service
from app.services.features import feature_service

router = APIRouter()


@router.get("/search")
async def search_cards(
    q: str,
    limit: int = 20,
    include_grades: bool = False,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Search for Pokemon cards - ALWAYS uses Pokemon TCG API for images."""
    query = q.strip()
    
    # ALWAYS use Pokemon TCG API for search (best images)
    try:
        tcg_results = await asyncio.wait_for(
            asyncio.to_thread(pokemon_tcg_service.search_cards, query, limit),
            timeout=20.0
        )
        
        if tcg_results:
            cards = [{
                "id": r.get("id"),
                "name": r.get("name"),
                "set_name": r.get("set_name", "Unknown"),
                "current_price": r.get("current_price", 0),
                "image_url": r.get("image_url"),
                "rarity": r.get("rarity"),
                "artist": r.get("artist"),
                "card_number": r.get("card_number"),
            } for r in tcg_results]
            
            if background_tasks:
                background_tasks.add_task(_save_pokemon_tcg_cards, tcg_results)
            
            return {"cards": cards, "count": len(cards), "source": "pokemon_tcg"}
    except asyncio.TimeoutError:
        import logging
        logging.getLogger(__name__).warning("Pokemon TCG API timeout")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Pokemon TCG search failed: {e}")
    
    # Fall back to database
    db_cards = db.query(Card).filter(
        or_(
            Card.name.ilike(f"%{query}%"),
            Card.set_name.ilike(f"%{query}%")
        )
    ).limit(limit).all()
    
    cards = []
    for card in db_cards:
        price = 0
        if card.features:
            price = card.features.current_price or 0
        cards.append({
            "id": card.external_id or str(card.id),
            "name": card.name,
            "set_name": card.set_name or "Unknown",
            "current_price": price,
            "image_url": card.image_url,
            "rarity": card.rarity,
        })
    
    return {"cards": cards, "count": len(cards), "source": "database"}


@router.get("/{card_id}")
async def get_card_detail(
    card_id: str,
    card_name: Optional[str] = None,
    set_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get card details using Pokemon TCG API for images and eBay for pricing."""
    # Check database first (fastest) - try external_id first, then internal id
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    # Also try internal ID if it looks like a number
    if not card and card_id.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id)).first()
    
    if not card:
        # Try Pokemon TCG API (with short timeout)
        card_data = None
        try:
            tcg_card = await asyncio.wait_for(
                asyncio.to_thread(pokemon_tcg_service.get_card_by_id, card_id),
                timeout=3.0
            )
            if tcg_card:
                card_data = {
                    "id": tcg_card.get("id"),
                    "product-name": tcg_card.get("name"),
                    "name": tcg_card.get("name"),
                    "console-name": tcg_card.get("set_name"),
                    "set_name": tcg_card.get("set_name"),
                    "rarity": tcg_card.get("rarity"),
                    "artist": tcg_card.get("artist"),
                    "number": tcg_card.get("card_number"),
                    "image": tcg_card.get("image_url"),
                    "tcgplayer_url": tcg_card.get("tcgplayer_url"),
                    "release_year": tcg_card.get("release_year"),
                    "loose-price": tcg_card.get("current_price", 0),
                }
        except (asyncio.TimeoutError, Exception):
            pass
        
        # Fallback to eBay if needed
        if not card_data and ebay_price_service.enabled and card_name:
            try:
                card_data = await asyncio.wait_for(
                    asyncio.to_thread(ebay_price_service.get_card_by_id, card_id, card_name, set_name),
                    timeout=3.0
                )
            except (asyncio.TimeoutError, Exception):
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Card not found")
        
        card = _create_card_from_api(db, card_id, card_data)
    
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    # Return immediately with database data, fetch prices in background would be slower
    # So we skip the eBay price fetch here for speed
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
        "tcgplayer_url": card.tcgplayer_url or _build_tcgplayer_url(card.name, card.set_name),
        "ebay_url": card.ebay_url or _build_ebay_url(card.name, card.set_name),
        "current_price": features.current_price if features else 0,
        "features": _format_features(features) if features else None,
    }


@router.get("/{card_id}/prices")
async def get_price_history(
    card_id: str,
    db: Session = Depends(get_db),
    price_db: Session = Depends(get_price_db),
    grade: Optional[str] = None,
    card_name: Optional[str] = None,
    set_name: Optional[str] = None,
):
    """Get price history for a card - uses PriceCharting for real eBay sold data."""
    import logging
    from app.services.pricecharting_scraper import pricecharting_scraper
    logger = logging.getLogger(__name__)
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    if not card and card_id.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id)).first()
    search_name = card_name or (card.name if card else None)
    search_set = set_name or (card.set_name if card else None)
    
    price_points = []
    
    # Use PriceCharting for accurate historical data
    if search_name:
        try:
            # Search for card on PriceCharting
            search_results = await asyncio.to_thread(
                pricecharting_scraper.search_card, search_name, search_set
            )
            
            if search_results:
                best_match = None
                for r in search_results:
                    if not r.get("is_first_edition"):
                        best_match = r
                        break
                if not best_match:
                    best_match = search_results[0]
                
                # Get sales history
                sales_by_grade = await asyncio.to_thread(
                    pricecharting_scraper.get_sales_history, best_match["url"]
                )
                
                # Map grade parameter to PriceCharting grade
                target_grade = grade if grade else "Ungraded"
                if target_grade == "Near Mint":
                    target_grade = "Ungraded"
                
                if target_grade in sales_by_grade:
                    sales = sales_by_grade[target_grade]
                    price_points = [{
                        "date": s["date"],
                        "price": s["price"],
                        "volume": 1,
                        "grade": target_grade,
                        "source": "pricecharting_ebay",
                    } for s in sales]
                    logger.info(f"Got {len(price_points)} points from PriceCharting for {search_name} {target_grade}")
        
        except Exception as e:
            logger.warning(f"PriceCharting failed: {e}")
    
    # Fallback to eBay if no PriceCharting data
    if len(price_points) < 3 and search_name and ebay_price_service.enabled:
        try:
            grade_param = grade if grade and grade != "Near Mint" else None
            
            ebay_history = await asyncio.wait_for(
                asyncio.to_thread(
                    ebay_price_service.build_price_history,
                    search_name,
                    search_set,
                    grade_param,
                    12
                ),
                timeout=8.0
            )
            
            if ebay_history:
                logger.info(f"Got {len(ebay_history)} points from eBay for {search_name}")
                existing_dates = {p["date"][:10] for p in price_points}
                for point in ebay_history:
                    if point["date"][:10] not in existing_dates:
                        price_points.append(point)
                price_points = sorted(price_points, key=lambda x: x["date"])
                
        except asyncio.TimeoutError:
            logger.warning(f"eBay price history timeout for {search_name}")
        except Exception as e:
            logger.warning(f"eBay price history error: {e}")
    
    return {"card_id": card_id, "prices": _aggregate_prices(price_points)}


@router.get("/{card_id}/grades")
async def get_prices_by_grade(
    card_id: str,
    card_name: Optional[str] = None,
    set_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get current prices for each PSA grade from eBay listings."""
    card = db.query(Card).filter(Card.external_id == card_id).first()
    if not card and card_id.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id)).first()
    
    name = card_name or (card.name if card else None)
    s_name = set_name or (card.set_name if card else None)
    
    if not name:
        raise HTTPException(status_code=400, detail="Card name required")
    
    if not ebay_price_service.enabled:
        raise HTTPException(status_code=503, detail="eBay API not configured")
    
    try:
        price_data = await asyncio.to_thread(
            ebay_price_service.get_card_prices, name, s_name
        )
        
        return {
            "card_id": card_id,
            "card_name": name,
            "set_name": s_name,
            "prices_by_grade": price_data.get("prices_by_grade", {}),
            "source": "ebay"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prices: {str(e)}")


@router.get("/{card_id}/all-grades-history")
async def get_all_grades_price_history(
    card_id: str,
    card_name: Optional[str] = None,
    set_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get REAL price history for ALL PSA grades from PriceCharting (eBay sold data)."""
    import logging
    from app.services.pricecharting_scraper import pricecharting_scraper
    logger = logging.getLogger(__name__)
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    if not card and card_id.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id)).first()
    name = card_name or (card.name if card else None)
    s_name = set_name or (card.set_name if card else None)
    
    if not name:
        raise HTTPException(status_code=400, detail="Card name required")
    
    results = {}
    data_source = "pricecharting"
    
    # Use PriceCharting for REAL historical data (actual eBay sold prices)
    try:
        logger.info(f"Getting PriceCharting data for {name} ({s_name})")
        
        # Search for the card
        search_results = await asyncio.to_thread(
            pricecharting_scraper.search_card, name, s_name
        )
        
        if search_results:
            # Find best match (prefer unlimited)
            best_match = None
            for r in search_results:
                if not r.get("is_first_edition"):
                    best_match = r
                    break
            if not best_match:
                best_match = search_results[0]
            
            card_url = best_match["url"]
            logger.info(f"Found card at: {card_url}")
            
            # Get all sales history
            sales_by_grade = await asyncio.to_thread(
                pricecharting_scraper.get_sales_history, card_url
            )
            
            # Process each grade
            for grade, sales in sales_by_grade.items():
                if not sales:
                    continue
                
                # Format history
                history = [{
                    "date": s["date"],
                    "price": s["price"],
                    "source": "pricecharting_ebay"
                } for s in sales]
                
                # Calculate stats
                prices = [s["price"] for s in sales]
                current_price = prices[-1] if prices else 0
                old_price = prices[0] if prices else 0
                
                change_pct = 0
                if old_price > 0 and len(prices) > 1:
                    change_pct = round(((current_price - old_price) / old_price) * 100, 2)
                
                results[grade] = {
                    "history": history,
                    "current_price": current_price,
                    "price_12m_ago": old_price,
                    "change_pct": change_pct,
                    "data_points": len(history),
                    "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
                    "source": "pricecharting_ebay",
                }
            
            logger.info(f"Got data for {len(results)} grades from PriceCharting")
            data_source = "pricecharting"
    
    except Exception as e:
        logger.error(f"PriceCharting failed: {e}")
        data_source = "ebay_fallback"
    
    # Fallback to eBay if PriceCharting didn't return data
    if not results and ebay_price_service.enabled:
        logger.info(f"Falling back to eBay for {name}")
        data_source = "ebay"
        grades = ["Near Mint"] + [f"PSA {g}" for g in range(1, 11)]
        
        async def fetch_ebay_grade(grade: str):
            try:
                grade_param = None if grade == "Near Mint" else grade
                history = await asyncio.wait_for(
                    asyncio.to_thread(
                        ebay_price_service.build_price_history,
                        name, s_name, grade_param, 12
                    ),
                    timeout=10.0
                )
                return grade, history
            except Exception as e:
                logger.warning(f"eBay failed for {grade}: {e}")
                return grade, []
        
        tasks = [fetch_ebay_grade(g) for g in grades]
        completed = await asyncio.gather(*tasks)
        
        for grade, history in completed:
            if history:
                results[grade] = {
                    "history": history,
                    "current_price": history[-1]["price"] if history else 0,
                    "price_12m_ago": history[0]["price"] if history else 0,
                    "change_pct": round(
                        ((history[-1]["price"] - history[0]["price"]) / history[0]["price"] * 100)
                        if history and history[0]["price"] > 0 else 0, 2
                    ),
                    "data_points": len(history),
                    "source": "ebay",
                }
    
    # Calculate investment recommendations
    recommendations = _calculate_grade_recommendations(results)
    
    return {
        "card_id": card_id,
        "card_name": name,
        "set_name": s_name,
        "grades": results,
        "recommendations": recommendations,
        "source": data_source
    }


def _calculate_grade_recommendations(grade_data: Dict) -> Dict:
    """Calculate which grades offer best investment value."""
    if not grade_data:
        return {}
    
    recommendations = {
        "best_value": None,
        "best_growth": None,
        "most_liquid": None,
        "analysis": []
    }
    
    best_value_score = -1
    best_growth = -999
    most_liquid = 0
    
    for grade, data in grade_data.items():
        if not data.get("history"):
            continue
            
        current = data.get("current_price", 0)
        change = data.get("change_pct", 0)
        points = data.get("data_points", 0)
        
        # Value score = growth potential relative to price
        # Lower grades with good growth = better value
        grade_num = 0
        if "PSA" in grade:
            try:
                grade_num = int(grade.split()[-1])
            except:
                pass
        
        # Best value: good growth at reasonable price point
        value_score = change / (current + 1) * 100 if current > 0 else 0
        if value_score > best_value_score and current > 0:
            best_value_score = value_score
            recommendations["best_value"] = grade
        
        # Best growth: highest % increase
        if change > best_growth:
            best_growth = change
            recommendations["best_growth"] = grade
        
        # Most liquid: most data points (more sales)
        if points > most_liquid:
            most_liquid = points
            recommendations["most_liquid"] = grade
        
        # Analysis entry
        analysis = {
            "grade": grade,
            "current_price": current,
            "growth_12m": change,
            "liquidity_score": points,
        }
        
        # Investment rating
        if change > 20 and points >= 3:
            analysis["rating"] = "Strong Buy"
        elif change > 10 and points >= 2:
            analysis["rating"] = "Buy"
        elif change > 0:
            analysis["rating"] = "Hold"
        elif change > -10:
            analysis["rating"] = "Underperform"
        else:
            analysis["rating"] = "Sell"
        
        recommendations["analysis"].append(analysis)
    
    # Sort analysis by growth
    recommendations["analysis"].sort(key=lambda x: x.get("growth_12m", 0), reverse=True)
    
    return recommendations


@router.get("/{card_id}/rating")
async def get_investment_rating(card_id: str, db: Session = Depends(get_db)):
    """Get investment rating for a card."""
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


def _create_card_from_api(db: Session, card_id: str, data: Dict) -> Card:
    """Create a card record from API data (eBay format)."""
    card_name = data.get("product-name") or data.get("name", "Unknown Card")
    set_name = data.get("console-name") or data.get("set_name", "Unknown")
    
    card = Card(
        external_id=card_id,
        name=card_name,
        set_name=set_name,
        rarity=data.get("rarity") or _extract_rarity(card_name),
        artist=data.get("artist") or _random_artist(),
        release_year=_extract_year(set_name),
        card_number=data.get("number"),
        image_url=data.get("image"),
        tcgplayer_url=_build_tcgplayer_url(card_name, set_name),
        ebay_url=_build_ebay_url(card_name, set_name)
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    
    # Get price - use ungraded price or from prices_by_grade
    current_price = data.get("loose-price", 0)
    prices_by_grade = data.get("prices_by_grade", {})
    if not current_price and prices_by_grade:
        # Try to get ungraded price first, then any grade price
        if "Ungraded" in prices_by_grade:
            current_price = prices_by_grade["Ungraded"].get("average_price", 0)
        elif prices_by_grade:
            # Use first available grade price
            first_grade = list(prices_by_grade.values())[0]
            current_price = first_grade.get("average_price", 0)
    
    if current_price > 0:
        _generate_price_history(db, card.id, current_price)
    
    # Create features
    features_dict = feature_service.create_card_features(card, current_price, [])
    db.add(CardFeature(card_id=card.id, **features_dict))
    db.commit()
    
    return card


def _generate_price_history(db: Session, card_id: int, current_price: float):
    """Generate estimated historical prices."""
    now = datetime.now()
    for months_ago in range(12, -1, -1):
        date = now - timedelta(days=months_ago * 30)
        progress = (12 - months_ago) / 12.0
        factor = 0.75 + (progress * 0.25)
        variance = 1.0 + (random.random() - 0.5) * 0.2
        price = current_price * factor * variance
        
        db.add(PriceHistory(
            card_id=card_id,
            date=date,
            price_loose=round(price, 2),
            volume=random.randint(5, 50),
            source="estimate"
        ))
    db.commit()


def _save_pokemon_tcg_cards(results: List[Dict]):
    """Save Pokemon TCG API results to database with proper images."""
    db = SessionLocal()
    try:
        for item in results:
            ext_id = item.get("id")
            if not ext_id:
                continue
            
            existing = db.query(Card).filter(Card.external_id == ext_id).first()
            if existing:
                # Update image if it's not from pokemontcg.io
                if existing.image_url and 'pokemontcg.io' not in existing.image_url:
                    existing.image_url = item.get("image_url")
                    db.commit()
                continue
            
            card = Card(
                external_id=ext_id,
                name=item.get("name", ""),
                set_name=item.get("set_name", "Unknown"),
                rarity=item.get("rarity"),
                artist=item.get("artist"),
                card_number=item.get("card_number"),
                release_year=item.get("release_year"),
                image_url=item.get("image_url"),  # Pokemon TCG API image
                tcgplayer_url=item.get("tcgplayer_url"),
            )
            db.add(card)
            db.flush()
            
            price = item.get("current_price", 0)
            if price > 0:
                db.add(PriceHistory(
                    card_id=card.id,
                    date=datetime.now(),
                    price_loose=price,
                    volume=0,
                    source="pokemon_tcg"
                ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _save_cards_to_db(results: List[Dict]):
    """Save eBay API results to database."""
    db = SessionLocal()
    try:
        for item in results:
            ext_id = item.get("id")
            if not ext_id:
                continue
            if db.query(Card).filter(Card.external_id == ext_id).first():
                continue
            
            card_name = item.get("product-name") or item.get("name", "")
            set_name = item.get("console-name") or item.get("set_name", "Unknown")
            
            card = Card(
                external_id=ext_id,
                name=card_name,
                set_name=set_name,
                rarity=item.get("rarity"),
                image_url=item.get("image")
            )
            db.add(card)
            db.flush()
            
            # Get price - prefer ungraded, then any available price
            price = item.get("loose-price", 0)
            prices_by_grade = item.get("prices_by_grade", {})
            if not price and prices_by_grade:
                if "Ungraded" in prices_by_grade:
                    price = prices_by_grade["Ungraded"].get("average_price", 0)
                elif prices_by_grade:
                    first_grade = list(prices_by_grade.values())[0]
                    price = first_grade.get("average_price", 0)
            
            if price > 0:
                db.add(PriceHistory(
                    card_id=card.id,
                    date=datetime.now(),
                    price_loose=price,
                    volume=0,
                    source="ebay"
                ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _aggregate_prices(points: List[Dict], max_points: int = 180) -> List[Dict]:
    """Aggregate price points by month."""
    if not points or len(points) <= max_points:
        return points
    
    by_month = defaultdict(list)
    for p in points:
        try:
            dt = datetime.fromisoformat(p["date"].replace("Z", "+00:00"))
            by_month[(dt.year, dt.month)].append(p)
        except Exception:
            continue
    
    aggregated = []
    for key in sorted(by_month.keys()):
        month_points = by_month[key]
        prices = [p["price"] for p in month_points if p["price"] > 0]
        if prices:
            mid = month_points[len(month_points) // 2]
            aggregated.append({
                "date": mid["date"],
                "price": round(median(prices), 2),
                "volume": mid.get("volume"),
                "grade": mid.get("grade"),
            })
    
    return aggregated


def _format_features(f: CardFeature) -> Dict:
    """Format features for response."""
    return {
        "popularity_score": f.popularity_score,
        "rarity_score": f.rarity_score,
        "artist_score": f.artist_score,
        "trend_30d": f.trend_30d,
        "trend_90d": f.trend_90d,
        "trend_1y": f.trend_1y,
        "volatility": f.price_volatility,
        "market_sentiment": f.market_sentiment,
        "investment_score": f.investment_score,
        "investment_rating": f.investment_rating
    }


def _extract_rarity(name: str) -> str:
    """Extract rarity from card name."""
    n = name.lower()
    if "holo" in n:
        return "Holo Rare"
    if "secret" in n:
        return "Secret Rare"
    if "rare" in n:
        return "Rare"
    return "Uncommon"


def _random_artist() -> str:
    """Get a random artist name."""
    return random.choice([
        "Ken Sugimori", "Mitsuhiro Arita", "Atsuko Nishida",
        "Kouki Saitou", "5ban Graphics", "Kagemaru Himeno"
    ])


def _extract_year(set_name: str) -> int:
    """Extract release year from set name."""
    s = set_name.lower()
    if "base" in s:
        return 1999
    if "fossil" in s or "jungle" in s:
        return 2000
    return random.randint(2018, 2024)


def _build_tcgplayer_url(name: Optional[str], set_name: Optional[str] = None) -> str:
    """Build TCGPlayer search URL."""
    q = " ".join(filter(None, [name, set_name])) or "pokemon card"
    return f"https://www.tcgplayer.com/search/pokemon/product?q={quote_plus(q)}&productLineName=pokemon"


def _build_ebay_url(name: Optional[str], set_name: Optional[str] = None) -> str:
    """Build eBay search URL."""
    q = " ".join(filter(None, [name, set_name, "pokemon card"]))
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(q)}"
