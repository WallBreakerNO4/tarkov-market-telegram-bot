import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    telegram_token: str
    tarkov_api_key: Optional[str] = None
    end_point_type: str = "pvp"
    cache_refresh_interval_seconds: int = 300
    cache_refresh_request_delay_seconds: float = 0.2


def load_config() -> Config:
    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tarkov_api_key = os.getenv("TARKOV_MARKET_API_TOKEN")
    end_point_type = os.getenv("END_POINT_TYPE", "pvp").lower()
    cache_refresh_interval_seconds_raw = os.getenv(
        "CACHE_REFRESH_INTERVAL_SECONDS", "300"
    )
    cache_refresh_request_delay_seconds_raw = os.getenv(
        "CACHE_REFRESH_REQUEST_DELAY_SECONDS", "0.2"
    )

    # print(f"Loaded Telegram Token: {'*' * len(telegram_token) if telegram_token else 'None'}")
    # print(f"Loaded Tarkov API Key: {'*' * len(tarkov_api_key) if tarkov_api_key else 'None'}")

    if not telegram_token:
        raise ValueError("Missing required environment variables")

    try:
        cache_refresh_interval_seconds = int(cache_refresh_interval_seconds_raw)
    except ValueError as e:
        raise ValueError(
            "Invalid CACHE_REFRESH_INTERVAL_SECONDS: must be an integer"
        ) from e

    try:
        cache_refresh_request_delay_seconds = float(
            cache_refresh_request_delay_seconds_raw
        )
    except ValueError as e:
        raise ValueError(
            "Invalid CACHE_REFRESH_REQUEST_DELAY_SECONDS: must be a number"
        ) from e

    if cache_refresh_interval_seconds <= 0:
        raise ValueError("Invalid CACHE_REFRESH_INTERVAL_SECONDS: must be > 0")

    if cache_refresh_request_delay_seconds < 0:
        raise ValueError("Invalid CACHE_REFRESH_REQUEST_DELAY_SECONDS: must be >= 0")

    return Config(
        telegram_token=telegram_token,
        tarkov_api_key=tarkov_api_key,
        end_point_type=end_point_type,
        cache_refresh_interval_seconds=cache_refresh_interval_seconds,
        cache_refresh_request_delay_seconds=cache_refresh_request_delay_seconds,
    )
