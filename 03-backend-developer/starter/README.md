# Стартовый скелет (FastAPI + SQLite)

Скелет нужен, чтобы не тратить время на настройку. Это подсказка, а не обязательная структура:
можно переименовывать файлы, выносить код в модули, взять другой Python-фреймворк (Flask, Django, Litestar)
или PostgreSQL вместо SQLite — тогда опишите запуск в README.

| Файл | Что это |
|---|---|
| `app/main.py` | приложение FastAPI: `/health` готов, обязательные эндпоинты — заглушки `501` с пометками `TODO` |
| `app/db.py` | подключение к SQLite (`GAMEGLORY_DB`, по умолчанию `gameglory.db`) и применение `schema.sql` |
| `app/schema.sql` | место для вашей схемы (что хранить — в комментариях) |
| `import_data.py` | заготовка импорта `games.csv` и `tags.csv` (разбор CSV готов, вставка — `TODO`) |
| `tests/test_api.py` | фикстура с временной БД и пример теста — добавьте свои 3–5 |
| `requirements.txt` | fastapi, uvicorn, pytest, httpx |

## Как запустить

Нужен Python 3.11+. SQLite встроен в Python (модуль `sqlite3`) — ставить ничего не нужно.

```bash
cd starter
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python import_data.py                     # создаёт gameglory.db из ../../shared-data
python import_data.py                     # повторный запуск: дублей быть не должно
uvicorn app.main:app --reload --port 8000 # Swagger UI: http://localhost:8000/docs

python -m pytest -q                       # ваши тесты
BASE_URL=http://localhost:8000 python -m pytest ../acceptance -q -rs   # приёмочные тесты
```

Путь к данным можно задать явно: `GAMEGLORY_DATA=<путь к shared-data> python import_data.py`.
Не коммитьте файл базы (`*.db`) и `.venv` — добавьте их в `.gitignore`.
