"""Приёмочные проверки дополнительной части: /health, /tags, /games/{id}/similar,
фильтры year_from / year_to, genre и platform, Swagger.

Каждый тест пропускается (skip), если эндпоинт отвечает 404/501 или необязательный фильтр
не реализован. Если же вы реализовали пункт, он проверяется по контракту так же строго,
как обязательная часть.
"""
from __future__ import annotations

import os

import pytest

from conftest import fetch_all, ids, require_endpoint, require_filter


# --------------------------------------------------------------------------- meta
def test_health(client):
    r = require_endpoint(client, "/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tags_dictionary(client, ref):
    r = require_endpoint(client, "/tags")
    assert r.status_code == 200
    items = r.json()["items"]
    assert {t["slug"] for t in items} == {t["slug"] for t in ref.tags}
    expected = {t["slug"]: t["games_count"] for t in ref.tags}
    for t in items:
        assert set(t) >= {"slug", "name", "category", "games_count"}
        assert t["games_count"] == expected[t["slug"]], t["slug"]
    keys = [(-t["games_count"], t["slug"]) for t in items]
    assert keys == sorted(keys), "теги должны быть отсортированы по games_count desc, slug asc"


@pytest.mark.skipif(os.environ.get("SKIP_DOCS_CHECK") == "1", reason="SKIP_DOCS_CHECK=1")
def test_swagger_available(client):
    require_endpoint(client, "/docs")
    spec = require_endpoint(client, "/openapi.json")
    assert spec.status_code == 200
    paths = spec.json().get("paths", {})
    for p in ["/games", "/games/{id}", "/niches/{tag}/stats"]:  # обязательные пути
        assert p in paths, f"в /openapi.json нет пути {p}"


# --------------------------------------------------------------------------- optional filters
def test_filter_year(client, ref):
    require_filter(client, len(ref.games), "year_from", "2018")
    params = {"tags": "survival", "price_min": 5, "price_max": 19.99, "year_from": 2018, "year_to": 2024}
    got = fetch_all(client, params)
    exp = ref.search(tags=["survival"], price_min=5, price_max=19.99, year_from=2018, year_to=2024)
    assert len(exp) > 0
    assert ids(got) == ids(exp)


@pytest.mark.parametrize("params", [{"year_from": 2024, "year_to": 2020}, {"year_from": 1969},
                                    {"year_to": 2101}, {"year_from": "abc"}])
def test_year_validation(client, ref, params):
    require_filter(client, len(ref.games), "year_from", "2018")
    r = client.get("/games", params=params)
    assert r.status_code == 422, f"{params} -> {r.status_code}"
    assert "detail" in r.json()


def test_filter_genre(client, ref):
    require_filter(client, len(ref.games), "genre", "Strategy")
    got = fetch_all(client, {"genre": "Strategy", "price_max": 0})
    exp = ref.search(genre="Strategy", price_max=0)
    assert len(exp) > 0
    assert ids(got) == ids(exp)


def test_filter_platform_combined(client, ref):
    require_filter(client, len(ref.games), "platform", "linux")
    params = {"tags": "survival", "price_min": 5, "price_max": 19.99, "platform": "linux"}
    got = fetch_all(client, params)
    exp = ref.search(tags=["survival"], price_min=5, price_max=19.99, platform="linux")
    assert ids(got) == ids(exp)


def test_platform_validation(client, ref):
    require_filter(client, len(ref.games), "platform", "linux")
    r = client.get("/games", params={"platform": "ps5"})
    assert r.status_code == 422
    assert "detail" in r.json()


# --------------------------------------------------------------------------- similar
def test_similar_matches_jaccard(client, ref):
    for g in ref.games[3::400]:
        r = require_endpoint(client, f"/games/{g['id']}/similar")
        assert r.status_code == 200
        body = r.json()
        assert body["game_id"] == g["id"]
        exp = ref.similar(g["id"], 10)
        got = [(it["game"]["id"], it["score"]) for it in body["items"]]
        assert [i for i, _ in got] == [i for i, _ in exp]
        for (_, s_got), (_, s_exp) in zip(got, exp):
            assert s_got == pytest.approx(s_exp, abs=1e-4)
        for it in body["items"]:
            assert it["game"]["id"] != g["id"]
            assert sorted(it["shared_tags"]) == it["shared_tags"]
            assert set(it["shared_tags"]) == set(g["tags"]) & set(ref.by_id[it["game"]["id"]]["tags"])


def test_similar_limit(client, ref):
    gid = ref.games[0]["id"]
    r = require_endpoint(client, f"/games/{gid}/similar", {"limit": 3})
    assert len(r.json()["items"]) == 3
    assert client.get(f"/games/{gid}/similar", params={"limit": 0}).status_code == 422
    assert client.get(f"/games/{gid}/similar", params={"limit": 51}).status_code == 422
    assert client.get("/games/1/similar").status_code == 404
