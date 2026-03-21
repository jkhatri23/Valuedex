"""In-memory card name -> card IDs index for instant search.

Uses an inverted token map for O(1) token lookups instead of scanning
every card name on each query.  Includes fuzzy fallback via
difflib so typos like "charizarq" still find "charizard".
"""

import logging
import re
from collections import defaultdict
from difflib import get_close_matches
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

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
                    "release_year": card.release_year,
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

    def _fuzzy_match_tokens(self, tokens: List[str], cutoff: float = 0.7) -> Tuple[List[str], bool]:
        """Try to correct each query token against the indexed vocabulary.
        Returns (corrected_tokens, was_corrected)."""
        all_indexed = list(self._token_to_keys.keys())
        if not all_indexed:
            return tokens, False

        corrected: List[str] = []
        changed = False
        for token in tokens:
            if token in self._token_to_keys:
                corrected.append(token)
                continue
            # Check if the token is a substring of any indexed token (already matched by _matching_keys)
            if any(token in idx_tok for idx_tok in all_indexed):
                corrected.append(token)
                continue
            matches = get_close_matches(token, all_indexed, n=1, cutoff=cutoff)
            if matches:
                corrected.append(matches[0])
                changed = True
            else:
                corrected.append(token)
        return corrected, changed

    def search(self, query: str, limit: int = 100) -> Tuple[List[dict], Optional[str]]:
        """Token-intersection search with alias expansion and fuzzy fallback.

        Returns (results, corrected_query) where corrected_query is the
        spell-corrected query string when the original had no exact matches,
        or None if no correction was needed.
        """
        q = _normalize(query)
        if not q:
            return [], None

        variants = _query_variants(q)
        matched_keys: Set[str] = set()
        for variant in variants:
            matched_keys |= self._matching_keys(variant)

        if matched_keys:
            results: List[dict] = []
            for key in sorted(matched_keys):
                results.extend(self._name_to_cards[key])
                if len(results) >= limit:
                    break
            return results[:limit], None

        # No exact matches — try fuzzy correction
        tokens = q.split()
        corrected_tokens, was_corrected = self._fuzzy_match_tokens(tokens)
        if not was_corrected:
            return [], None

        corrected_query = " ".join(corrected_tokens)
        corrected_variants = _query_variants(corrected_query)
        for variant in corrected_variants:
            matched_keys |= self._matching_keys(variant)

        results = []
        for key in sorted(matched_keys):
            results.extend(self._name_to_cards[key])
            if len(results) >= limit:
                break

        if results:
            logger.info(f"Fuzzy corrected '{q}' -> '{corrected_query}' ({len(results)} results)")
            return results[:limit], corrected_query

        return [], None

card_index = CardIndex()
