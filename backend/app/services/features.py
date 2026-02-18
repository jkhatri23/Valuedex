"""Feature calculation for cards."""

from typing import Dict
import random
from app.models.card import Card


class FeatureService:
    """Calculate features for ML model and investment ratings."""
    
    RARITY_SCORES = {
        # Standard rarities
        "common": 1.0,
        "uncommon": 2.5,
        "rare": 4.0,
        "holo rare": 6.0,
        "reverse holo": 5.0,
        "rare holo": 6.0,
        # Modern ultra/premium rarities
        "ultra rare": 8.0,
        "rare ultra": 8.0,
        "rare holo v": 7.0,
        "rare holo vmax": 8.0,
        "rare holo vstar": 7.5,
        "rare holo gx": 7.5,
        "rare holo ex": 7.0,
        "double rare": 7.5,
        # High-end rarities
        "secret rare": 9.5,
        "hyper rare": 9.5,
        "special art rare": 9.5,
        "illustration rare": 9.0,
        "special illustration rare": 10.0,
        "full art": 8.5,
        "rare secret": 9.5,
        "rare rainbow": 9.0,
        "rare shiny": 8.0,
        "shiny rare": 8.0,
        "shiny holo rare": 8.5,
        "amazing rare": 8.0,
        "radiant rare": 7.5,
        # Legacy/promo rarities
        "ace spec rare": 8.5,
        "rare ace": 8.5,
        "promo": 5.5,
        "rare promo": 6.0,
        "classic collection": 7.0,
        "legend": 9.0,
        "rare break": 7.0,
        "rare prime": 7.5,
        "rare lv.x": 8.0,
    }
    
    POKEMON_POPULARITY = {
        # Gen 1 - Icons & starters
        "charizard": 100, "pikachu": 95, "mewtwo": 90, "mew": 90,
        "blastoise": 82, "venusaur": 80, "dragonite": 78,
        "gyarados": 75, "snorlax": 72, "eevee": 78,
        "arcanine": 73, "alakazam": 72, "machamp": 68,
        "ninetales": 70, "lapras": 70, "aerodactyl": 65,
        "zapdos": 74, "moltres": 72, "articuno": 72,
        "hitmonlee": 55, "hitmonchan": 55, "electabuzz": 58,
        "magmar": 55, "jolteon": 70, "flareon": 68, "vaporeon": 68,
        "nidoking": 62, "nidoqueen": 58, "clefairy": 50,
        "wigglytuff": 48, "vileplume": 48, "poliwrath": 50,
        "golem": 50, "slowbro": 52, "magneton": 52,
        "dodrio": 42, "dewgong": 42, "hypno": 45,
        "exeggutor": 48, "chansey": 55, "kangaskhan": 55,
        "starmie": 52, "scyther": 62, "pinsir": 55,
        "tauros": 50, "ditto": 60, "porygon": 55,
        "kabutops": 58, "omastar": 55,
        # Gen 1 - Evolutions & fan favorites
        "gengar": 80, "haunter": 55, "gastly": 45,
        "charmander": 65, "charmeleon": 55,
        "squirtle": 62, "wartortle": 50,
        "bulbasaur": 60, "ivysaur": 48,
        "pidgeot": 50, "raichu": 62, "clefable": 52,
        # Gen 2
        "lugia": 85, "ho-oh": 83, "celebi": 75,
        "tyranitar": 78, "typhlosion": 72, "feraligatr": 68,
        "meganium": 60, "scizor": 72, "heracross": 62,
        "espeon": 85, "umbreon": 88, "suicune": 73,
        "entei": 72, "raikou": 70, "ampharos": 65,
        "steelix": 62, "kingdra": 62, "houndoom": 62,
        "togetic": 55, "crobat": 58, "pichu": 60,
        "togepi": 58, "marill": 48, "murkrow": 50,
        "slowking": 52, "wobbuffet": 50, "sneasel": 55,
        "skarmory": 58, "donphan": 55, "porygon2": 52,
        "blissey": 58, "larvitar": 55, "pupitar": 48,
        # Gen 3
        "rayquaza": 85, "groudon": 78, "kyogre": 78,
        "blaziken": 75, "swampert": 70, "sceptile": 68,
        "gardevoir": 80, "salamence": 72, "metagross": 72,
        "latias": 68, "latios": 68, "jirachi": 65,
        "deoxys": 65, "absol": 65, "flygon": 62,
        "milotic": 65, "altaria": 58, "aggron": 60,
        "manectric": 52, "wailord": 55, "breloom": 55,
        "zangoose": 50, "banette": 52, "dusclops": 50,
        "tropius": 45, "relicanth": 48, "beldum": 52,
        # Gen 4
        "lucario": 82, "garchomp": 78, "darkrai": 80,
        "dialga": 75, "palkia": 72, "giratina": 78,
        "arceus": 82, "shaymin": 60, "infernape": 68,
        "empoleon": 62, "torterra": 60, "luxray": 65,
        "togekiss": 62, "leafeon": 65, "glaceon": 65,
        "gallade": 62, "electivire": 58, "magmortar": 55,
        "rhyperior": 55, "weavile": 60, "honchkrow": 55,
        "spiritomb": 55, "roserade": 52, "drapion": 48,
        "rotom": 60, "manaphy": 55, "cresselia": 58,
        "heatran": 55, "regigigas": 55,
        # Gen 5
        "reshiram": 72, "zekrom": 72, "kyurem": 68,
        "zoroark": 70, "hydreigon": 65, "volcarona": 62,
        "genesect": 60, "meloetta": 52, "keldeo": 55,
        "victini": 58, "serperior": 52, "emboar": 50,
        "samurott": 52, "chandelure": 60, "haxorus": 58,
        "excadrill": 55, "krookodile": 52, "reuniclus": 48,
        "zorua": 55, "bisharp": 55, "braviary": 50,
        # Gen 6
        "greninja": 82, "xerneas": 65, "yveltal": 65,
        "zygarde": 55, "sylveon": 78, "trevenant": 50,
        "aegislash": 58, "goodra": 52, "noivern": 55,
        "delphox": 52, "chesnaught": 48, "hawlucha": 50,
        "diancie": 55, "hoopa": 52, "volcanion": 48,
        # Gen 7
        "solgaleo": 62, "lunala": 62, "necrozma": 60,
        "mimikyu": 75, "decidueye": 60, "incineroar": 58,
        "primarina": 55, "toxapex": 52, "lycanroc": 55,
        "tapu koko": 55, "tapu lele": 52, "buzzwole": 50,
        "zeraora": 55, "marshadow": 55, "melmetal": 52,
        # Gen 8
        "zacian": 65, "zamazenta": 60, "eternatus": 55,
        "dragapult": 62, "urshifu": 58, "cinderace": 55,
        "rillaboom": 50, "inteleon": 50, "toxtricity": 55,
        "corviknight": 52, "grimmsnarl": 50, "calyrex": 55,
        # Gen 9
        "miraidon": 65, "koraidon": 65, "meowscarada": 58,
        "skeledirge": 52, "quaquaval": 50, "palafin": 48,
        "gholdengo": 55, "annihilape": 52, "baxcalibur": 50,
        "terapagos": 52, "ogerpon": 55, "pecharunt": 48,
        "roaring moon": 55, "iron valiant": 52,
    }
    
    ARTIST_SCORES = {
        # Legendary-tier (original designers, most iconic art)
        "ken sugimori": 9.5,
        "mitsuhiro arita": 9.5,
        "atsuko nishida": 9.0,
        # Master-tier (highly sought after, premium art)
        "hyogonosuke": 9.0,
        "naoki saito": 9.0,
        "anesaki dynamic": 8.5,
        "akira komayama": 8.5,
        "kouki saitou": 8.5,
        "ryo ueda": 8.5,
        "yuka morii": 8.5,
        "shin nagasawa": 8.5,
        "sowsow": 8.5,
        "sanosuke sakuma": 8.5,
        # Elite-tier (well-known, strong collector appeal)
        "5ban graphics": 8.0,
        "planeta": 8.0,
        "planeta igarashi": 8.0,
        "planeta mochizuki": 8.0,
        "planeta tsuji": 8.0,
        "kawayoo": 8.0,
        "kanako eo": 8.0,
        "hajime kusajima": 8.0,
        "masakazu fukuda": 8.0,
        "tomokazu komiya": 8.0,
        "takeshi shudo": 8.0,
        "sui": 8.0,
        "saya tsuruta": 8.0,
        "hitoshi ariga": 8.0,
        "kagemaru himeno": 8.0,
        "ayaka yoshida": 8.0,
        # Established-tier (recognized, consistent quality)
        "noriko takaya": 7.5,
        "eri yamaki": 7.5,
        "hisao nakamura": 7.5,
        "keiji kinebuchi": 7.5,
        "yumi": 7.5,
        "akira egawa": 7.5,
        "naoyo kimura": 7.5,
        "tokiya sakuba": 7.5,
        "miki tanaka": 7.5,
        "ryuta fuse": 7.5,
        "satoshi shirai": 7.5,
        "taira akitsu": 7.5,
        "mizue": 7.5,
        "asako ito": 7.5,
        "hasuno": 7.5,
        "kurumi tamiya": 7.5,
        "teeziro": 7.5,
        "uninori": 7.5,
        "jiro sasumo": 7.5,
        # Solid-tier (good artists with moderate collector premium)
        "megumi mizutani": 7.0,
        "sumiyoshi kizuki": 7.0,
        "kouki saitou": 7.0,
        "kyoko umemoto": 7.0,
        "hideki kazama": 7.0,
        "shiburingaru": 7.0,
        "nagimiso": 7.0,
        "oku": 7.0,
        "yoriyuki ikegami": 7.0,
        "oswaldo kato": 7.0,
        "yukiko baba": 7.0,
        "shibuzoh": 7.0,
        "reflex": 7.0,
        "gemi": 7.0,
        "akari mikazuki": 7.0,
        "chibi": 7.0,
        "jerky": 7.0,
        "tika matsuno": 7.0,
    }
    
    def calculate_rarity_score(self, rarity: str) -> float:
        if not rarity:
            return 3.0
        rarity_lower = rarity.lower()
        # Try exact match first, then substring match (longest key first to avoid partial hits)
        sorted_keys = sorted(self.RARITY_SCORES.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in rarity_lower:
                return self.RARITY_SCORES[key]
        return 3.0
    
    def calculate_popularity_score(self, name: str) -> float:
        if not name:
            return 50.0
        name_lower = name.lower()
        for pokemon, score in self.POKEMON_POPULARITY.items():
            if pokemon in name_lower:
                return float(score)
        # Heuristic bump for card name indicators of collector value
        base = 45.0
        if any(tag in name_lower for tag in ["ex", "gx", "v ", "vmax", "vstar"]):
            base += 10.0
        if any(tag in name_lower for tag in ["full art", "alt art", "special art"]):
            base += 8.0
        if "gold" in name_lower or "rainbow" in name_lower:
            base += 5.0
        return min(base, 80.0)
    
    def calculate_artist_score(self, artist: str) -> float:
        if not artist:
            return 5.0
        artist_lower = artist.lower()
        for known, score in self.ARTIST_SCORES.items():
            if known in artist_lower:
                return score
        return 5.0
    
    def calculate_investment_score(
        self, price: float, rarity: float, popularity: float,
        artist: float, trend_30d: float, trend_1y: float, volatility: float
    ) -> tuple[float, str]:
        """Calculate investment score (1-10) and rating."""
        fundamentals = (rarity / 10) * 0.4 + (popularity / 100) * 0.4 + (artist / 10) * 0.2
        momentum = max(0, min(1, (trend_1y + 30) / 70))
        stability = max(0, min(1, 1 - (volatility / 50)))
        
        score = (fundamentals * 5 + momentum * 3 + stability * 2)
        score = max(1.0, min(10.0, score))
        
        if score >= 8.5:
            rating = "Strong Buy"
        elif score >= 7.0:
            rating = "Buy"
        elif score >= 5.5:
            rating = "Hold"
        elif score >= 4.0:
            rating = "Underperform"
        else:
            rating = "Sell"
        
        return round(score, 2), rating
    
    def create_card_features(self, card: Card, current_price: float, price_history: list) -> Dict:
        """Create features for a card."""
        rarity = self.calculate_rarity_score(card.rarity)
        popularity = self.calculate_popularity_score(card.name)
        artist = self.calculate_artist_score(card.artist)
        
        trend_30d = random.uniform(-5, 15)
        trend_90d = random.uniform(-3, 20)
        trend_1y = random.uniform(0, 30)
        volatility = random.uniform(5, 25)
        sentiment = random.uniform(40, 70)
        
        score, rating = self.calculate_investment_score(
            current_price, rarity, popularity, artist, trend_30d, trend_1y, volatility
        )
        
        return {
            "popularity_score": popularity,
            "rarity_score": rarity,
            "artist_score": artist,
            "current_price": current_price,
            "price_volatility": volatility,
            "trend_30d": trend_30d,
            "trend_90d": trend_90d,
            "trend_1y": trend_1y,
            "market_sentiment": sentiment,
            "investment_score": score,
            "investment_rating": rating,
        }


feature_service = FeatureService()
