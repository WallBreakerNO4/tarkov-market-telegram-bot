import requests
from libs.config import Config

class TarkovMarketAPI:
    BASE_URL_PVP = "https://api.tarkov-market.app/api/v1"
    BASE_URL_PVE = "https://api.tarkov-market.app/api/v1/pve"
    
    def __init__(self, config: Config):
        self.api_key = config.tarkov_api_key
        self.end_point_type = config.end_point_type
        self.base_url = (
            self.BASE_URL_PVE if self.end_point_type == "pve"
            else self.BASE_URL_PVP
        )
        print(f"当前API端点模式: {self.end_point_type.upper()}")
        
    def search_item(self, item_name: str):
        headers = {"x-api-key": self.api_key}
        params = {"q": item_name}
        
        try:
            response = requests.get(
                f"{self.base_url}/item",
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
                f"{self.base_url}/item",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None