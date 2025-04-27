import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    telegram_token: str
    tarkov_api_key: str

def load_config() -> Config:
    load_dotenv()
    
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tarkov_api_key = os.getenv("TARKOV_MARKET_API_TOKEN")
    
    # print(f"Loaded Telegram Token: {'*' * len(telegram_token) if telegram_token else 'None'}")
    # print(f"Loaded Tarkov API Key: {'*' * len(tarkov_api_key) if tarkov_api_key else 'None'}")
    
    if not telegram_token or not tarkov_api_key:
        raise ValueError("Missing required environment variables")
        
    return Config(
        telegram_token=telegram_token,
        tarkov_api_key=tarkov_api_key
    )