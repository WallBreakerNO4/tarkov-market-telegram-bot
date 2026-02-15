import logging
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from libs.tarkov_api import TarkovMarketAPI


logger = logging.getLogger(__name__)


LANGUAGES = [
    "cs",
    "de",
    "en",
    "es",
    "fr",
    "hu",
    "it",
    "ja",
    "ko",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "tr",
    "zh",
]


class SqliteItemCache:
    def __init__(self, db_path: str = "db.sqlite3", ttl_seconds: int = 300):
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self._refresh_lock = threading.Lock()

        with self._connect() as conn:
            self._ensure_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER,
                avg24h_price INTEGER,
                trader_name TEXT,
                trader_price INTEGER
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS item_names (
                item_id TEXT NOT NULL,
                lang TEXT NOT NULL,
                name TEXT NOT NULL,
                normalized_name TEXT,
                short_name TEXT,
                PRIMARY KEY (item_id, lang)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_item_names_name ON item_names(name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_item_names_normalized_name ON item_names(normalized_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_item_names_short_name ON item_names(short_name)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def _get_meta(self, conn: sqlite3.Connection, key: str) -> Optional[str]:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        value = row[0]
        return value if isinstance(value, str) else None

    def _set_meta(self, conn: sqlite3.Connection, key: str, value: str) -> None:
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def _refreshed_at(self) -> Optional[int]:
        with self._connect() as conn:
            self._ensure_schema(conn)
            raw = self._get_meta(conn, "refreshed_at")
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def is_fresh(self) -> bool:
        refreshed_at = self._refreshed_at()
        if refreshed_at is None:
            return False
        return (int(time.time()) - refreshed_at) <= self.ttl_seconds

    def refresh_all(self, api: TarkovMarketAPI) -> None:
        items = api.fetch_all_items(limit=10000)
        if not items:
            raise RuntimeError("全量刷新失败：API 未返回 items")

        names_rows = []
        for lang in LANGUAGES:
            names = api.fetch_all_item_names(lang=lang, limit=10000)
            if not names:
                raise RuntimeError(f"全量刷新失败：API 未返回 item names (lang={lang})")

            for item in names:
                item_id = item.get("uid")
                name = item.get("name")
                if not isinstance(item_id, str) or not item_id:
                    continue
                if not isinstance(name, str) or not name:
                    continue
                normalized_name = item.get("normalizedName")
                short_name = item.get("shortName")
                names_rows.append(
                    (
                        item_id,
                        lang,
                        name,
                        normalized_name if isinstance(normalized_name, str) else None,
                        short_name if isinstance(short_name, str) else None,
                    )
                )

        now = str(int(time.time()))
        rows = [
            (
                item.get("uid"),
                item.get("name"),
                item.get("price"),
                item.get("avg24hPrice"),
                item.get("traderName"),
                item.get("traderPrice"),
            )
            for item in items
            if isinstance(item.get("uid"), str) and isinstance(item.get("name"), str)
        ]

        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN")
            conn.execute("DELETE FROM items")
            conn.execute("DELETE FROM item_names")
            conn.executemany(
                """
                INSERT INTO items(id, name, price, avg24h_price, trader_name, trader_price)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.executemany(
                """
                INSERT INTO item_names(item_id, lang, name, normalized_name, short_name)
                VALUES(?, ?, ?, ?, ?)
                """,
                names_rows,
            )
            self._set_meta(conn, "refreshed_at", now)
            conn.commit()

        logger.info(
            "全量刷新成功：写入 %d 条 items, %d 条 item_names",
            len(rows),
            len(names_rows),
        )

    def _query_by_name(
        self, conn: sqlite3.Connection, item_name: str, limit: int
    ) -> List[Dict[str, Any]]:
        name = item_name.strip()
        if not name:
            return []

        def _display_name(item_id: str) -> str:
            row = conn.execute(
                "SELECT name FROM item_names WHERE item_id = ? AND lang = 'zh' LIMIT 1",
                (item_id,),
            ).fetchone()
            if row and isinstance(row[0], str) and row[0]:
                return row[0]
            row = conn.execute(
                "SELECT name FROM item_names WHERE item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
            if row and isinstance(row[0], str) and row[0]:
                return row[0]
            return name

        def _item_row(item_id: str) -> Optional[sqlite3.Row]:
            return conn.execute(
                """
                SELECT id, price, avg24h_price, trader_name, trader_price
                FROM items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()

        exact_ids = conn.execute(
            """
            SELECT
              n.item_id,
              MIN(LENGTH(n.name)) AS name_len
            FROM item_names n
            WHERE
              n.name = ? COLLATE NOCASE OR
              n.normalized_name = ? COLLATE NOCASE
            GROUP BY n.item_id
            ORDER BY name_len ASC
            LIMIT ?
            """,
            (name, name, limit),
        ).fetchall()

        if exact_ids:
            item_ids = [row[0] for row in exact_ids if isinstance(row[0], str)]
        else:
            like = f"%{name}%"
            like_ids = conn.execute(
                """
                SELECT
                  n.item_id,
                  MIN(
                    CASE
                      WHEN n.name LIKE ? COLLATE NOCASE THEN 0
                      WHEN n.normalized_name LIKE ? COLLATE NOCASE THEN 1
                      WHEN n.short_name LIKE ? COLLATE NOCASE THEN 2
                      ELSE 3
                    END
                  ) AS match_rank,
                  MIN(
                    CASE
                      WHEN n.name LIKE '%half%' COLLATE NOCASE THEN 1
                      ELSE 0
                    END
                  ) AS half_penalty,
                  MIN(LENGTH(n.name)) AS name_len
                FROM item_names n
                WHERE
                  n.name LIKE ? COLLATE NOCASE OR
                  n.short_name LIKE ? COLLATE NOCASE OR
                  n.normalized_name LIKE ? COLLATE NOCASE
                GROUP BY n.item_id
                ORDER BY match_rank ASC, half_penalty ASC, name_len ASC
                LIMIT ?
                """,
                (like, like, like, like, like, like, limit),
            ).fetchall()
            item_ids = [row[0] for row in like_ids if isinstance(row[0], str)]

        results: List[Dict[str, Any]] = []
        for item_id in item_ids:
            raw = _item_row(item_id)
            if not raw:
                continue

            item: Dict[str, Any] = {
                "uid": item_id,
                "name": _display_name(item_id),
            }

            price = raw[1]
            avg24h_price = raw[2]
            trader_name = raw[3]
            trader_price = raw[4]

            if isinstance(price, int):
                item["price"] = price
            if isinstance(avg24h_price, int):
                item["avg24hPrice"] = avg24h_price
            if isinstance(trader_name, str) and trader_name:
                item["traderName"] = trader_name
            if isinstance(trader_price, int):
                item["traderPrice"] = trader_price

            results.append(item)

        return results

    def search_items(
        self, item_name: str, api: TarkovMarketAPI, limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        if not self.is_fresh():
            with self._refresh_lock:
                if not self.is_fresh():
                    self.refresh_all(api)

        if not self.is_fresh():
            raise RuntimeError("缓存刷新后仍不可用")

        with self._connect() as conn:
            self._ensure_schema(conn)
            results = self._query_by_name(conn, item_name, limit)

        return results or None
