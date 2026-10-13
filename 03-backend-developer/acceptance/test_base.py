"""Приёмочные проверки обязательной части (shared-data/mock-api/openapi.yaml):
GET /games, GET /games/{id}, GET /niches/{tag}/stats и валидация входа.

Запуск против запущенного сервиса:
    pip install -r acceptance/requirements.txt
    BASE_URL=http://localhost:8000 pytest acceptance -q

Ожидаемые значения рассчитываются по shared-data/games.csv, поэтому сервис должен быть
загружен ровно этим датасетом (seed по умолчанию).
"""
from __future__ import annotations

import time

import pytest

from conftest import fetch_all, ids

SUMMARY_KEYS = {"id", "title", "developer", "publisher", "release_date", "price_usd", "tags", "genres",
                "reviews_total", "reviews_positive_ratio", "platforms"}
DETAIL_KEYS = SUMMARY_KEYS | {"short_description", "estimated_owners_range"}
SAMPLE_IDS_COUNT = 5


# --------------------------------------------------------------------------- /games
def test_games_default_page(client, ref):
    r = client.get("/games")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"items", "total", "page", "page_size"}
    assert body["total"] == len(ref.games)
    assert body["page"] == 1 and body["page_size"] == 20
    assert len(body["items"]) == 20
    for g in body["items"]:
        assert set(g) >= SUMMARY_KEYS
        assert isinstance(g["tags"], list) and isinstance(g["platforms"], list)
    assert ids(body["items"]) == ids(ref.search()[:20]), "сортировка по умолчанию: -reviews_total, затем id asc"


def test_pagination_slices(client, ref):
    expected = ids(ref.search())
    r1 = client.get("/games", params={"page": 2, "page_size": 7}).json()
    r2 = client.get("/games", params={"page": 3, "page_size": 7}).json()
    assert ids(r1["items"]) == expected[7:14]
    assert ids(r2["items"]) == expected[14:21]
    assert r1["page"] == 2 and r1["page_size"] == 7


def test_page_out_of_range_is_empty(client, ref):
    r = client.get("/games", params={"page": 10_000, "page_size": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == [] and body["total"] == len(ref.games)


@pytest.mark.parametrize("q", ["lantern", "LANTERN", "  of  ", "zzzz-no-such-title"])
def test_search_by_title_case_insensitive(client, ref, q):
    got = fetch_all(client, {"q": q})
    exp = ref.search(q=q)
    assert sorted(ids(got)) == sorted(ids(exp))


def test_filter_tags_and_semantics(client, ref):
    got = fetch_all(client, {"tags": "roguelike,deckbuilding"})
    exp = ref.search(tags=["roguelike", "deckbuilding"])
    assert len(exp) > 0
    assert ids(got) == ids(exp)
    for g in got:
        assert {"roguelike", "deckbuilding"} <= set(g["tags"])


def test_unknown_tag_returns_empty(client):
    r = client.get("/games", params={"tags": "no-such-tag"})
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_filter_price(client, ref):
    params = {"tags": "survival", "price_min": 5, "price_max": 19.99}
    got = fetch_all(client, params)
    exp = ref.search(tags=["survival"], price_min=5, price_max=19.99)
    assert len(exp) > 0
    assert ids(got) == ids(exp)


def test_filter_free_games(client, ref):
    got = fetch_all(client, {"price_max": 0})
    exp = ref.search(price_max=0)
    assert len(exp) > 0
    assert ids(got) == ids(exp)


@pytest.mark.parametrize("sort", ["price_usd", "-price_usd", "release_date", "-release_date", "reviews_total",
                                  "reviews_positive_ratio", "-reviews_positive_ratio", "title", "-title"])
def test_sorting(client, ref, sort):
    r = client.get("/games", params={"sort": sort, "page_size": 50, "page": 2})
    assert r.status_code == 200, r.text
    assert ids(r.json()["items"]) == ids(ref.search(sort=sort)[50:100])


@pytest.mark.parametrize("sort", ["title", "-title"])
def test_sort_by_title_full_order(client, ref, sort):
    """Полный порядок по названию без учёта регистра, при равенстве — по id."""
    got = fetch_all(client, {"sort": sort})
    assert ids(got) == ids(ref.search(sort=sort))


def test_ratio_sort_puts_nulls_last(client, ref):
    total = len(ref.games)
    for sort in ["reviews_positive_ratio", "-reviews_positive_ratio"]:
        last_page = client.get("/games", params={"sort": sort, "page_size": 100,
                                                 "page": (total + 99) // 100}).json()["items"]
        assert last_page[-1]["reviews_positive_ratio"] is None, sort


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page": "abc"}, {"page_size": 0}, {"page_size": 101},
    {"page": 10_001}, {"page": "99999999999999999999"},
    {"price_min": -1}, {"price_min": 20, "price_max": 10}, {"price_max": "cheap"},
    {"price_max": 10_001}, {"price_max": "inf"}, {"price_min": "nan"}, {"price_max": "1e400"},
    {"q": ""}, {"q": "   "}, {"q": "x" * 101},
    {"sort": "bogus"}, {"sort": "-developer"}, {"sort": "id;DROP TABLE games"},
])
def test_games_validation(client, params):
    r = client.get("/games", params=params)
    assert r.status_code == 422, f"{params} -> {r.status_code}"
    assert "detail" in r.json()


# --------------------------------------------------------------------------- /games/{id}
def test_game_card_matches_dataset(client, ref):
    sample = ref.games[:: len(ref.games) // SAMPLE_IDS_COUNT][:SAMPLE_IDS_COUNT]
    sample.append(next(g for g in ref.games if g["reviews_positive_ratio"] is None))
    for g in sample:
        r = client.get(f"/games/{g['id']}")
        assert r.status_code == 200
        body = r.json()
        assert set(body) >= DETAIL_KEYS
        for k in DETAIL_KEYS:
            if k == "price_usd" or (k == "reviews_positive_ratio" and g[k] is not None):
                assert body[k] == pytest.approx(g[k], abs=1e-6), k
            elif k in ("tags", "genres", "platforms"):
                assert sorted(body[k]) == sorted(g[k]), k
            else:
                assert body[k] == g[k], k


def test_game_not_found(client):
    r = client.get("/games/1")
    assert r.status_code == 404
    assert isinstance(r.json().get("detail"), str)


def test_game_bad_id(client):
    assert client.get("/games/not-a-number").status_code in (404, 422)
    for bad in ["0", "-5", "99999999999999999999"]:
        r = client.get(f"/games/{bad}")
        assert r.status_code == 422, f"/games/{bad} -> {r.status_code}"


# --------------------------------------------------------------------------- niches
@pytest.mark.parametrize("tag", ["roguelike", "farming", "multiplayer", "4x", "free-to-play"])
def test_niche_stats(client, ref, tag):
    r = client.get(f"/niches/{tag}/stats")
    assert r.status_code == 200
    body = r.json()
    exp = ref.niche(tag)
    assert body["tag"] == tag
    assert body["games_count"] == exp["games_count"]
    assert body["median_price_usd"] == pytest.approx(exp["median_price_usd"], abs=0.006)
    assert body["median_reviews_total"] == pytest.approx(exp["median_reviews_total"], abs=0.01)
    assert body["mean_positive_ratio"] == pytest.approx(exp["mean_positive_ratio"], abs=0.0011)
    assert body["releases_by_year"] == exp["releases_by_year"]
    assert body["price_distribution"] == exp["price_distribution"]
    assert sum(b["count"] for b in body["price_distribution"]) == body["games_count"]


def test_niche_unknown_tag(client):
    r = client.get("/niches/definitely-not-a-tag/stats")
    assert r.status_code == 404
    assert "detail" in r.json()


# --------------------------------------------------------------------------- smoke perf
def test_basic_latency(client):
    """Мягкая проверка: типичные запросы на 2000 играх должны укладываться в 1 секунду."""
    for path, params in [("/games", {"tags": "roguelike", "sort": "-price_usd"}),
                         ("/games", {"q": "the", "price_min": 5}),
                         ("/niches/multiplayer/stats", {})]:
        t0 = time.perf_counter()
        assert client.get(path, params=params).status_code == 200
        assert time.perf_counter() - t0 < 1.0, path
