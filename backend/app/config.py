from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "sqlite:///./pokedict.db"
    price_database_url: str = "sqlite:///./pricepoints.db"
    pricecharting_api_key: str = ""  # Used for Pokemon TCG API key (pokemontcg.io)
    pokemon_tcg_api_key: str = ""  # Alternative name for the same key
    ebay_app_id: str = ""
    ebay_dev_id: str = ""
    ebay_cert_id: str = ""
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

