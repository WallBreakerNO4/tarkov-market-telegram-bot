import requests
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from libs.config import Config


class TarkovMarketAPI:
    GRAPHQL_URL = "https://api.tarkov.dev/graphql"

    def __init__(self, config: "Config"):
        self.api_key = config.tarkov_api_key
        self.end_point_type = config.end_point_type
        self.game_mode = "pve" if self.end_point_type == "pve" else "regular"
        self.lang = "zh"
        print(f"当前API端点模式: {self.end_point_type.upper()}")

    def _post_graphql(self, query: str, variables: dict, timeout: int = 10):
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()

            errors = payload.get("errors")
            if errors:
                message = (
                    errors[0].get("message")
                    if isinstance(errors, list)
                    else str(errors)
                )
                raise requests.exceptions.RequestException(message or "GraphQL error")

            return payload.get("data")
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"API请求失败: {e}")
            return None

    def _get_avg7days_price(self, item_id: str):
        query = """
query Item7DaysAvg($id: ID!, $lang: LanguageCode, $gameMode: GameMode) {
  historicalItemPrices(id: $id, days: 7, lang: $lang, gameMode: $gameMode) {
    price
    timestamp
  }
}
"""
        data = self._post_graphql(
            query,
            {"id": item_id, "lang": self.lang, "gameMode": self.game_mode},
        )
        if not data:
            return None

        points = data.get("historicalItemPrices") or []
        prices: List[int] = []
        for point in points:
            if not isinstance(point, dict):
                continue
            price = point.get("price")
            if isinstance(price, int):
                prices.append(price)
        if not prices:
            return None

        return int(round(sum(prices) / len(prices)))

    def _best_trader_sell_for(self, sell_for):
        if not isinstance(sell_for, list):
            return None, None

        best = None
        for entry in sell_for:
            if not isinstance(entry, dict):
                continue
            if entry.get("source") == "fleaMarket":
                continue
            price = entry.get("price")
            if not isinstance(price, int):
                continue
            best_price = best.get("price") if isinstance(best, dict) else None
            if best is None or (isinstance(best_price, int) and price > best_price):
                best = entry

        if not best:
            return None, None

        vendor = best.get("vendor") if isinstance(best.get("vendor"), dict) else None
        trader_name = (vendor or {}).get("name") or best.get("source")
        return trader_name, best.get("price")

    def search_item(self, item_name: str):
        query = """
query SearchItems($name: String!, $lang: LanguageCode, $gameMode: GameMode, $limit: Int) {
  items(name: $name, lang: $lang, gameMode: $gameMode, limit: $limit) {
    id
    name
    avg24hPrice
    lastLowPrice
    sellFor {
      price
      source
      vendor {
        name
        normalizedName
      }
    }
  }
}
"""
        data = self._post_graphql(
            query,
            {
                "name": item_name,
                "lang": self.lang,
                "gameMode": self.game_mode,
                "limit": 5,
            },
        )
        if not data:
            return None

        items = data.get("items") or []
        if not items:
            return None

        results = []
        for raw in items:
            if not isinstance(raw, dict):
                continue

            item_id = raw.get("id")
            name = raw.get("name")
            if not isinstance(item_id, str) or not item_id:
                continue
            if not isinstance(name, str) or not name:
                continue

            item: Dict[str, Any] = {"uid": item_id, "name": name}

            last_low_price = raw.get("lastLowPrice")
            if isinstance(last_low_price, int):
                item["price"] = last_low_price

            avg24h_price = raw.get("avg24hPrice")
            if isinstance(avg24h_price, int):
                item["avg24hPrice"] = avg24h_price

            trader_name, trader_price = self._best_trader_sell_for(raw.get("sellFor"))
            if trader_name is not None:
                item["traderName"] = trader_name
            if trader_price is not None:
                item["traderPrice"] = trader_price

            results.append(item)

        if not results:
            return None

        first_uid = results[0].get("uid")
        avg7 = (
            self._get_avg7days_price(first_uid) if isinstance(first_uid, str) else None
        )
        if avg7 is not None:
            results[0]["avg7daysPrice"] = avg7

        return results

    def fetch_all_items(self, limit: int = 10000):
        query = """
query AllItems($lang: LanguageCode, $gameMode: GameMode, $limit: Int, $offset: Int) {
  items(lang: $lang, gameMode: $gameMode, limit: $limit, offset: $offset) {
    id
    name
    avg24hPrice
    lastLowPrice
    sellFor {
      price
      source
      vendor {
        name
        normalizedName
      }
    }
  }
}
"""
        data = self._post_graphql(
            query,
            {
                "lang": self.lang,
                "gameMode": self.game_mode,
                "limit": limit,
                "offset": 0,
            },
            timeout=30,
        )
        if not data:
            return None

        items = data.get("items") or []
        if not items:
            return None

        results = []
        for raw in items:
            if not isinstance(raw, dict):
                continue

            item_id = raw.get("id")
            name = raw.get("name")
            if not isinstance(item_id, str) or not item_id:
                continue
            if not isinstance(name, str) or not name:
                continue

            item: Dict[str, Any] = {"uid": item_id, "name": name}

            last_low_price = raw.get("lastLowPrice")
            if isinstance(last_low_price, int):
                item["price"] = last_low_price

            avg24h_price = raw.get("avg24hPrice")
            if isinstance(avg24h_price, int):
                item["avg24hPrice"] = avg24h_price

            trader_name, trader_price = self._best_trader_sell_for(raw.get("sellFor"))
            if trader_name is not None:
                item["traderName"] = trader_name
            if trader_price is not None:
                item["traderPrice"] = trader_price

            results.append(item)

        return results or None

    def fetch_all_item_names(self, lang: str, limit: int = 10000):
        query = """
query AllItemNames($lang: LanguageCode, $gameMode: GameMode, $limit: Int, $offset: Int) {
  items(lang: $lang, gameMode: $gameMode, limit: $limit, offset: $offset) {
    id
    name
    normalizedName
    shortName
  }
}
"""
        data = self._post_graphql(
            query,
            {
                "lang": lang,
                "gameMode": self.game_mode,
                "limit": limit,
                "offset": 0,
            },
            timeout=30,
        )
        if not data:
            return None

        items = data.get("items") or []
        if not items:
            return None

        results = []
        for raw in items:
            if not isinstance(raw, dict):
                continue

            item_id = raw.get("id")
            name = raw.get("name")
            if not isinstance(item_id, str) or not item_id:
                continue
            if not isinstance(name, str) or not name:
                continue

            item: Dict[str, Any] = {
                "uid": item_id,
                "name": name,
            }

            normalized_name = raw.get("normalizedName")
            if isinstance(normalized_name, str) and normalized_name:
                item["normalizedName"] = normalized_name

            short_name = raw.get("shortName")
            if isinstance(short_name, str) and short_name:
                item["shortName"] = short_name

            results.append(item)

        return results or None

    def get_item_by_uid(self, uid: str):
        query = """
query GetItem($id: ID!, $lang: LanguageCode, $gameMode: GameMode) {
  item(id: $id, lang: $lang, gameMode: $gameMode) {
    id
    name
    avg24hPrice
    lastLowPrice
    sellFor {
      price
      source
      vendor {
        name
        normalizedName
      }
    }
  }
}
"""
        data = self._post_graphql(
            query,
            {"id": uid, "lang": self.lang, "gameMode": self.game_mode},
        )
        if not data:
            return None

        raw = data.get("item")
        if not isinstance(raw, dict):
            return None

        item_id = raw.get("id")
        name = raw.get("name")
        if not isinstance(item_id, str) or not item_id:
            return None
        if not isinstance(name, str) or not name:
            return None

        item: Dict[str, Any] = {"uid": item_id, "name": name}

        last_low_price = raw.get("lastLowPrice")
        if isinstance(last_low_price, int):
            item["price"] = last_low_price

        avg24h_price = raw.get("avg24hPrice")
        if isinstance(avg24h_price, int):
            item["avg24hPrice"] = avg24h_price

        trader_name, trader_price = self._best_trader_sell_for(raw.get("sellFor"))
        if trader_name is not None:
            item["traderName"] = trader_name
        if trader_price is not None:
            item["traderPrice"] = trader_price

        avg7 = self._get_avg7days_price(item_id)
        if avg7 is not None:
            item["avg7daysPrice"] = avg7

        return [item]
