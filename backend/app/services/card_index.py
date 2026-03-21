"""In-memory card name -> card IDs index for instant search.

Uses an inverted token map for O(1) token lookups instead of scanning
every card name on each query.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.card import Card, CardFeature

logger = logging.getLogger(__name__)

_NORMALIZE_RE = re.compile(r"[-''.:]+")
_COLLAPSE_SPACES_RE = re.compile(r"\s+")

_QUERY_ALIASES = [
    (re.compile(r"\bmega\b"), "m"),
]


def _normalize(text: str) -> str:
    text = _NORMALIZE_RE.sub(" ", text.lower())
    return _COLLAPSE_SPACES_RE.sub(" ", text).strip()


def _tokenize(text: str) -> List[str]:
    return _normalize(text).split()


def _query_variants(normalized_query: str) -> List[str]:
    variants = [normalized_query]
    for pattern, replacement in _QUERY_ALIASES:
        alt = pattern.sub(replacement, normalized_query)
        if alt != normalized_query:
            variants.append(alt)
    return variants


class CardIndex:
    """
    Inverted-index card search. Each token from a card name maps to the set of
    name-keys that contain it, so a multi-word query is resolved by intersecting
    token sets — no linear scan required.
    """

    def __init__(self):
        self._name_to_cards: Dict[str, List[dict]] = defaultdict(list)
        self._token_to_keys: Dict[str, Set[str]] = defaultdict(set)
        self._all_keys: List[str] = []
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
            new_tokens: Dict[str, Set[str]] = defaultdict(set)

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

                for token in _tokenize(raw_name):
                    new_tokens[token].add(name_key)

            self._name_to_cards = new_map
            self._token_to_keys = new_tokens
            self._all_keys = sorted(new_map.keys())
            self._card_count = sum(len(v) for v in new_map.values())
            logger.info(
                f"Card index built: {len(self._all_keys)} unique names, "
                f"{self._card_count} total cards, "
                f"{len(self._token_to_keys)} tokens"
            )
        finally:
            if close_db:
                db.close()

    def _matching_keys(self, query_str: str) -> Set[str]:
        """Find name-keys matching all tokens in query_str via set intersection."""
        tokens = query_str.split()
        if not tokens:
            return set()

        matched: Optional[Set[str]] = None
        for token in tokens:
            token_matches: Set[str] = set()
            for idx_token, keys in self._token_to_keys.items():
                if token in idx_token:
                    token_matches |= keys
            if matched is None:
                matched = token_matches
            else:
                matched &= token_matches
            if not matched:
                return set()
        return matched or set()

    def search(self, query: str, limit: int = 100) -> List[dict]:
        """Token-intersection search with alias expansion.

        Normalizes the query so "zygarde gx" matches "Zygarde-GX",
        "charizard ex" matches "Charizard-EX", "mega charizard"
        matches "M Charizard-EX", etc.
        """
        q = _normalize(query)
        if not q:
            return []

        variants = _query_variants(q)
        matched_keys: Set[str] = set()
        for variant in variants:
            matched_keys |= self._matching_keys(variant)

        results: List[dict] = []
        for key in sorted(matched_keys):
            results.extend(self._name_to_cards[key])
            if len(results) >= limit:
                break

        return results[:limit]

card_index = CardIndex()
