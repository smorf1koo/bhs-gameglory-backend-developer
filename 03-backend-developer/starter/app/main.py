"""Gameglory catalog API - starter skeleton (FastAPI + SQLite).

Contract: ../../shared-data/mock-api/openapi.yaml. Required endpoints are below;
replace each `raise HTTPException(501, ...)` with an implementation.

Run:  uvicorn app.main:app --reload --port 8000   (Swagger UI: http://localhost:8000/docs)
"""
from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from app.db import connect

app = FastAPI(title="Gameglory Catalog API", version="1.0.0")

# Allowed sort fields (prefix "-" means descending). Never put user input into SQL text directly.
SORT_FIELDS = {"title", "release_date", "price_usd", "reviews_total", "reviews_positive_ratio"}


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


Db = Annotated[sqlite3.Connection, Depends(get_db)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/games")
def search_games(
    db: Db,
    q: str | None = None,
    tags: str | None = Query(None, description="comma-separated tag slugs, AND semantics"),
    price_min: float | None = None,
    price_max: float | None = None,
    sort: str = "-reviews_total",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    # TODO: filters, sorting (tie-break by id, NULL last), pagination -> {items, total, page, page_size}
    # TODO: validation (422) - ranges and upper bounds from the contract, blank q,
    #       price_min <= price_max, sort whitelist
    raise HTTPException(501, "Not implemented yet")


@app.get("/games/{id}")
def get_game(id: int, db: Db) -> dict:
    # TODO: full game card or 404 {"detail": "..."}; id outside 1..2147483647 -> 422
    raise HTTPException(501, "Not implemented yet")


@app.get("/niches/{tag}/stats")
def niche_stats(tag: str, db: Db) -> dict:
    # TODO: games_count, medians, mean ratio, releases_by_year (no gaps), 6 price buckets; 404 for unknown tag
    #       (the stats may be computed in Python from rows selected by SQL)
    raise HTTPException(501, "Not implemented yet")
