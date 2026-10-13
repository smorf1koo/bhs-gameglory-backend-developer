"""Общие фикстуры приёмочных тестов контракта Gameglory Catalog API.

test_base.py     — обязательная часть задания (должна проходить у базового решения);
test_optional.py — необязательные эндпоинты и фильтры: тест пропускается (skip), если сервис
                   отвечает 404/501 (эндпоинт не реализован) или игнорирует необязательный фильтр.

Переменные окружения:
  BASE_URL          адрес запущенного сервиса (по умолчанию http://localhost:8000)
  GAMEGLORY_DATA    каталог shared-data с games.csv/tags.csv (по умолчанию ../../shared-data)
  SKIP_DOCS_CHECK=1 пропустить проверку Swagger (необязательная часть)
"""
from __future__ import annotations

import csv
import os
import statistics
from pathlib import Path

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
DATA_DIR = Path(os.environ.get("GAMEGLORY_DATA", Path(__file__).resolve().parents[2] / "shared-data"))
SEP = "|"


def _load_games() -> list[dict]:
    path = DATA_DIR / "games.csv"
    if not path.exists():
        pytest.exit(f"Не найден {path}. Укажите GAMEGLORY_DATA=<путь к shared-data>", returncode=2)
    games = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            games.append({
                "id": int(r["id"]),
                "title": r["title"],
                "developer": r["developer"],
                "publisher": r["publisher"],
                "release_date": r["release_date"],
                "price_usd": float(r["price_usd"]),
                "tags": r["tags"].split(SEP) if r["tags"] else [],
                "genres": r["genres"].split(SEP) if r["genres"] else [],
                "short_description": r["short_description"],
                "reviews_total": int(r["reviews_total"]),
                "reviews_positive_ratio": float(r["reviews_positive_ratio"]) if r["reviews_positive_ratio"] else None,
                "platforms": r["platforms"].split(SEP) if r["platforms"] else [],
                "estimated_owners_range": r["estimated_owners_range"],
            })
    return games


def _load_tags() -> list[dict]:
    with (DATA_DIR / "tags.csv").open(encoding="utf-8") as f:
        return [{**r, "games_count": int(r["games_count"])} for r in csv.DictReader(f)]


class Reference:
    """Ожидаемые ответы API, посчитанные по правилам контракта прямо из CSV."""

    BUCKETS = [("free", lambda p: p == 0), ("0-5", lambda p: 0 < p < 5), ("5-10", lambda p: 5 <= p < 10),
               ("10-20", lambda p: 10 <= p < 20), ("20-30", lambda p: 20 <= p < 30), ("30+", lambda p: p >= 30)]

    def __init__(self, games: list[dict], tags: list[dict]):
        self.games = games
        self.by_id = {g["id"]: g for g in games}
        self.tags = tags

    def search(self, q=None, tags=(), genre=None, platform=None, price_min=None, price_max=None,
               year_from=None, year_to=None, sort="-reviews_total") -> list[dict]:
        res = []
        for g in self.games:
            y = int(g["release_date"][:4])
            if q and q.strip().lower() not in g["title"].lower():
                continue
            if any(t not in g["tags"] for t in tags):
                continue
            if genre and genre not in g["genres"]:
                continue
            if platform and platform not in g["platforms"]:
                continue
            if price_min is not None and g["price_usd"] < price_min:
                continue
            if price_max is not None and g["price_usd"] > price_max:
                continue
            if year_from is not None and y < year_from:
                continue
            if year_to is not None and y > year_to:
                continue
            res.append(g)
        desc = sort.startswith("-")
        field = sort.lstrip("-")
        res.sort(key=lambda g: g["id"])
        present = [g for g in res if g[field] is not None]
        missing = [g for g in res if g[field] is None]
        key = (lambda g: g[field].lower()) if field == "title" else (lambda g: g[field])
        present.sort(key=key, reverse=desc)  # стабильная сортировка сохраняет порядок по id
        return present + missing

    def similar(self, gid: int, limit: int = 10) -> list[tuple[int, float]]:
        a = set(self.by_id[gid]["tags"])
        scored = []
        for g in self.games:
            if g["id"] == gid:
                continue
            b = set(g["tags"])
            inter = a & b
            if inter:
                scored.append((len(inter) / len(a | b), g))
        scored.sort(key=lambda x: (-x[0], -x[1]["reviews_total"], x[1]["id"]))
        return [(g["id"], s) for s, g in scored[:limit]]

    def niche(self, tag: str) -> dict:
        sub = [g for g in self.games if tag in g["tags"]]
        prices = [g["price_usd"] for g in sub]
        ratios = [g["reviews_positive_ratio"] for g in sub if g["reviews_positive_ratio"] is not None]
        years = [int(g["release_date"][:4]) for g in sub]
        return {
            "games_count": len(sub),
            "median_price_usd": statistics.median(prices),
            "median_reviews_total": statistics.median([g["reviews_total"] for g in sub]),
            "mean_positive_ratio": sum(ratios) / len(ratios) if ratios else None,
            "releases_by_year": [{"year": y, "count": years.count(y)} for y in range(min(years), max(years) + 1)],
            "price_distribution": [{"bucket": b, "count": sum(1 for p in prices if f(p))} for b, f in self.BUCKETS],
        }


@pytest.fixture(scope="session")
def ref() -> Reference:
    return Reference(_load_games(), _load_tags())


def ids(items):
    return [g["id"] for g in items]


def fetch_all(client, params: dict) -> list[dict]:
    """Обходит все страницы выдачи /games."""
    out, page = [], 1
    while True:
        r = client.get("/games", params={**params, "page": page, "page_size": 100})
        assert r.status_code == 200, r.text
        body = r.json()
        out.extend(body["items"])
        if not body["items"] or len(out) >= body["total"]:
            return out
        page += 1


NOT_IMPLEMENTED = (404, 501)


def require_endpoint(client: httpx.Client, path: str, params: dict | None = None) -> httpx.Response:
    """GET необязательного эндпоинта; 404/501 на заведомо существующем объекте -> skip."""
    r = client.get(path, params=params)
    if r.status_code in NOT_IMPLEMENTED:
        pytest.skip(f"необязательный эндпоинт {path} не реализован ({r.status_code})")
    return r


def require_filter(client: httpx.Client, total_games: int, name: str, value: str) -> None:
    """Пропускает тест, если необязательный фильтр не реализован (отклонён или проигнорирован)."""
    r = client.get("/games", params={name: value, "page_size": 1})
    if r.status_code in (400, 422, 501):
        pytest.skip(f"необязательный фильтр {name} не поддерживается ({r.status_code})")
    if r.status_code == 200 and r.json().get("total") == total_games:
        pytest.skip(f"необязательный фильтр {name} не реализован (параметр игнорируется)")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        try:
            c.get("/games", params={"page_size": 1})
        except httpx.HTTPError as e:
            pytest.exit(f"Сервис недоступен по {BASE_URL}: {e}", returncode=2)
        yield c
