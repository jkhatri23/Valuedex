#!/usr/bin/env python3
"""
Check if Blaine's Charizard mock data exists in the database.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.price_database import PriceSessionLocal
from app.models.card import Card, PriceHistory
from app.models.price_point import PricePoint

EXTERNAL_ID = "gym2-2"

def check_data():
    db = SessionLocal()
    price_db = PriceSessionLocal()
    
    try:
        # Check if card exists
        card = db.query(Card).filter(Card.external_id == EXTERNAL_ID).first()
        if not card:
            print(f"❌ Card not found with external_id: {EXTERNAL_ID}")
            return
        
        print(f"✅ Card found: {card.name} (ID: {card.id})")
        print(f"   External ID: {card.external_id}")
        
        # Check price history
        history_count = db.query(PriceHistory).filter(PriceHistory.card_id == card.id).count()
        print(f"\n📊 Price History records: {history_count}")
        
        if history_count > 0:
            first = db.query(PriceHistory).filter(PriceHistory.card_id == card.id).order_by(PriceHistory.date.asc()).first()
            last = db.query(PriceHistory).filter(PriceHistory.card_id == card.id).order_by(PriceHistory.date.desc()).first()
            print(f"   First: {first.date.strftime('%Y-%m-%d')} - ${first.price_loose}")
            print(f"   Last:  {last.date.strftime('%Y-%m-%d')} - ${last.price_loose}")
        
        # Check price points
        points_count = price_db.query(PricePoint).filter(PricePoint.card_external_id == EXTERNAL_ID).count()
        print(f"\n📈 Price Points records: {points_count}")
        
        if points_count > 0:
            grades = price_db.query(PricePoint.grade).filter(PricePoint.card_external_id == EXTERNAL_ID).distinct().all()
            print(f"   Grades: {[g[0] or 'Ungraded' for g in grades]}")
            
            for grade, in grades:
                count = price_db.query(PricePoint).filter(
                    PricePoint.card_external_id == EXTERNAL_ID,
                    PricePoint.grade == grade
                ).count()
                grade_label = grade or "Ungraded"
                print(f"   {grade_label}: {count} points")
        
    finally:
        db.close()
        price_db.close()

if __name__ == "__main__":
    check_data()
