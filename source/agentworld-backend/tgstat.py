"""Small client for the TGStat API (https://api.tgstat.ru/docs).

Used endpoints:
  channels/search       find channels by keyword or category
  channels/stat         subscribers, average post reach, ERR, ER, citation index
  channels/subscribers  subscriber count per day (to spot sudden spikes)
  database/categories   list of category codes (run `python tgstat.py categories`)

Every call costs requests on your TGStat plan, so the Scout only fetches details
for channels that pass the size filter.
"""
import sys
import time
from typing import Any

import httpx

from config import settings

BASE = "https://api.tgstat.ru"


class TGStatError(RuntimeError):
    pass


class TGStat:
    def __init__(self, token: str | None = None, timeout: float = 20.0):
        self.token = token or settings.tgstat_token
        if not self.token:
            raise TGStatError("TGSTAT_TOKEN is not set")
        self.http = httpx.Client(base_url=BASE, timeout=timeout)

    def _get(self, path: str, **params: Any) -> Any:
        params = {k: v for k, v in params.items() if v not in (None, "")}
        params["token"] = self.token
        for attempt in range(3):
            r = self.http.get(path, params=params)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            if data.get("status") != "ok":
                raise TGStatError(f"{path}: {data.get('error', data)}")
            return data["response"]
        raise TGStatError(f"{path}: gave up after retries (HTTP {r.status_code})")

    def search(self, q: str | None = None, category: str | None = None, limit: int = 50) -> list[dict]:
        """Channels matching a keyword (min 3 characters) and/or a category."""
        resp = self._get(
            "/channels/search",
            q=q,
            category=category or settings.tgstat_category,
            country=settings.tgstat_country,
            language=settings.tgstat_language,
            peer_type="channel",
            search_by_description=1,
            limit=min(limit, 100),
        )
        return resp.get("items", [])

    def stat(self, channel: str) -> dict:
        return self._get("/channels/stat", channelId=channel)

    def subscribers(self, channel: str, days: int = 30) -> list[dict]:
        """[{'period': 'YYYY-MM-DD', 'participants_count': n}, ...] newest first."""
        start = int(time.time()) - days * 86400
        return self._get("/channels/subscribers", channelId=channel, startDate=start, group="day")

    def categories(self) -> list[dict]:
        return self._get("/database/categories", lang="en")

    def countries(self) -> list[dict]:
        return self._get("/database/countries", lang="en")

    def languages(self) -> list[dict]:
        return self._get("/database/languages", lang="en")


if __name__ == "__main__":
    # Helper: print the codes to put in TGSTAT_CATEGORY / TGSTAT_COUNTRY / TGSTAT_LANGUAGE
    what = sys.argv[1] if len(sys.argv) > 1 else "categories"
    api = TGStat()
    for item in getattr(api, what)():
        print(item)
