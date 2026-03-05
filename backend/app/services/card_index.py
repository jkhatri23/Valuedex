"""In-memory card name -> card IDs index for instant search."""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.card import Card, CardFeature

logger = logging.getLogger(__name__)

_NORMALIZE_RE = re.compile(r"[-''.:]+")
_COLLAPSE_SPACES_RE = re.compile(r"\s+")

# Aliases that users might type vs. what appears in card names.
# Applied to the search query so "mega charizard" -> also tries "m charizard".
_QUERY_ALIASES = [
    (re.compile(r"\bmega\b"), "m"),
]


def _normalize(text: str) -> str:
    """Normalize a card name or query for matching.

    Strips hyphens / punctuation and collapses whitespace so that both
    "Zygarde-GX" and the user query "zygarde gx" become "zygarde gx".
    """
    text = _NORMALIZE_RE.sub(" ", text.lower())
    return _COLLAPSE_SPACES_RE.sub(" ", text).strip()


def _query_variants(normalized_query: str) -> List[str]:
    """Return the query plus any alias-expanded variants.

    e.g. "mega charizard ex" -> ["mega charizard ex", "m charizard ex"]
    """
    variants = [normalized_query]
    for pattern, replacement in _QUERY_ALIASES:
        alt = pattern.sub(replacement, normalized_query)
        if alt != normalized_query:
            variants.append(alt)
    return variants


class CardIndex:
    """
    Maps normalized card names to lists of card data dicts.
    Enables sub-millisecond search by doing a simple substring match
    against pre-built keys instead of hitting an external API.
    """

    def __init__(self):
        self._name_to_cards: Dict[str, List[dict]] = defaultdict(list)
        self._search_keys: List[Tuple[str, str]] = []
        self._card_count = 0

    @property
    def size(self) -> int:
        return self._card_count

    def build(self, db: Optional[Session] = None):
        """Load every card from the database into the index."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            cards = (
                db.query(Card, CardFeature.current_price)
                .outerjoin(CardFeature, CardFeature.card_id == Card.id)
                .all()
            )

            new_map: Dict[str, List[dict]] = defaultdict(list)

            for card, price in cards:
                raw_name = (card.name or "").strip()
                if not raw_name:
                    continue

                name_key = raw_name.lower()

                new_map[name_key].append({
                    "id": card.external_id or str(card.id),
                    "name": card.name,
                    "set_name": card.set_name or "Unknown",
                    "current_price": price or 0,
                    "image_url": card.image_url,
                    "rarity": card.rarity,
                    "artist": card.artist,
                    "card_number": card.card_number,
                })

            self._name_to_cards = new_map
            # Store both the original key and the normalized form for matching
            self._search_keys = sorted(
                [(key, _normalize(key)) for key in new_map.keys()],
                key=lambda t: t[1],
            )
            self._card_count = sum(len(v) for v in new_map.values())
            logger.info(
                f"Card index built: {len(self._search_keys)} unique names, "
                f"{self._card_count} total cards"
            )
        finally:
            if close_db:
                db.close()

    def search(self, query: str, limit: int = 20) -> List[dict]:
        """Fast substring search against the index.

        Normalizes the query so "zygarde gx" matches "Zygarde-GX",
        "charizard ex" matches "Charizard-EX", "mega charizard"
        matches "M Charizard-EX", etc.
        """
        q = _normalize(query)
        if not q:
            return []

        variants = _query_variants(q)
        seen_keys: set = set()
        results: List[dict] = []

        for original_key, normalized_key in self._search_keys:
            if original_key in seen_keys:
                continue
            for variant in variants:
                if variant in normalized_key:
                    seen_keys.add(original_key)
                    results.extend(self._name_to_cards[original_key])
                    break
            if len(results) >= limit:
                break

        return results[:limit]

card_index = CardIndex()
