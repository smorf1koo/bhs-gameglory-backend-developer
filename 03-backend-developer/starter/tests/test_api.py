"""Example tests. Add 3-5 of your own: filters, sorting, medians, 404/422."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.db as db_module
from import_data import DEFAULT_DATA, import_data


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """A fresh SQLite database built from shared-data for the whole test session."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    import_data(DEFAULT_DATA, db_path)
    db_module.DB_PATH = db_path
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# TODO: for example
# def test_import_is_idempotent(client): ...
# def test_tags_filter_is_and(client): ...
# def test_game_not_found(client): ...
