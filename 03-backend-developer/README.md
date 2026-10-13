# Gameglory · Backend Developer · «API каталога игр»

Тестовое задание на позицию Backend Developer (стажёр / джун) в проекте Gameglory, Bear Head Studio.
Нужно импортировать ~2000 игр в SQLite и реализовать три эндпоинта по готовому контракту OpenAPI:
`GET /games` (поиск, фильтры, сортировка, пагинация), `GET /games/{id}` и `GET /niches/{tag}/stats`.

Задание — в документе
[`Тестовое_задание_Backend_Developer.docx`](Тестовое_задание_Backend_Developer.docx).

## Состав пакета

| Путь | Что это |
|---|---|
| `Тестовое_задание_Backend_Developer.docx` | задание: задача, входные данные, что сделать, как сдать |
| `starter/` | скелет FastAPI + SQLite: `/health` готов, обязательные эндпоинты — заглушки 501, заготовки импорта и тестов |
| `acceptance/` | приёмочные тесты: `test_base.py` — обязательная часть, `test_optional.py` — дополнительная |
| `requests.http` | примеры запросов: сначала обязательные, в конце — необязательные |
| `../shared-data/` | данные (`games.csv`, `tags.csv`, `schema.md`) и контракт API `mock-api/openapi.yaml` |

## Как начать

```bash
cd starter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python import_data.py && uvicorn app.main:app --reload --port 8000
```

Подробнее — в `starter/README.md` и `acceptance/README.md`.
