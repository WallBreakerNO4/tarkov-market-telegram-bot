import requests
from libs.config import Config

class TarkovMarketAPI:
    BASE_URL = "https://api.tarkov-market.app/api/v1"
    
    def __init__(self, config: Config):
        self.api_key = config.tarkov_api_key
        
    def search_item(self, item_name: str):
        headers = {"x-api-key": self.api_key}
        params = {"q": item_name}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/item",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None

    def get_item_by_uid(self, uid: str):
        headers = {"x-api-key": self.api_key}
        params = {"uid": uid}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/item",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None