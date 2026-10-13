# Приёмочные проверки контракта (acceptance)

pytest-тесты проверяют запущенный сервис «чёрным ящиком» по HTTP на соответствие контракту
`../../shared-data/mock-api/openapi.yaml`. Ожидаемые значения рассчитываются прямо из
`shared-data/games.csv` и `tags.csv`, поэтому сервис должен быть загружен **ровно этим** датасетом.

| Файл | Что проверяет |
|---|---|
| `test_base.py` | **обязательная часть**: `GET /games` (поиск `q`, фильтры `tags`, `price_min/max`, сортировка, пагинация), `GET /games/{id}`, `GET /niches/{tag}/stats`, валидация (422/404), мягкая проверка задержки |
| `test_optional.py` | дополнительная часть: `/health`, `/tags`, `/games/{id}/similar`, фильтры `year_from/to`, `genre` и `platform`, Swagger (`/docs`, `/openapi.json`) |

Тесты из `test_optional.py` **пропускаются (skip)**, если эндпоинт отвечает `404`/`501` или
необязательный фильтр не реализован (сервис его игнорирует). Базовое решение должно проходить
`test_base.py` целиком; пропуски в `test_optional.py` — нормально.

## Запуск

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r acceptance/requirements.txt

# сервис запущен, например: uvicorn app.main:app --port 8000
BASE_URL=http://localhost:8000 pytest acceptance -q -rs     # -rs покажет причины пропусков
```

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BASE_URL` | `http://localhost:8000` | адрес сервиса |
| `GAMEGLORY_DATA` | `../../shared-data` относительно папки тестов | где лежат `games.csv`, `tags.csv` |
| `SKIP_DOCS_CHECK` | — | `1` — пропустить проверку Swagger |

Если вы скопировали тесты в свой репозиторий, укажите `GAMEGLORY_DATA=<путь к shared-data>`.

## Что ещё учесть

- Прохождение тестов — **необходимое, но не достаточное** условие: проверяющие смотрят также
  схему БД, импорт, код, ваши тесты, README и защиту.
- Не меняйте тесты «под себя». Если считаете, что тест противоречит контракту, опишите ситуацию
  в README решения.
