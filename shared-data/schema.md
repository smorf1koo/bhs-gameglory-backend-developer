# Схема данных shared-data

> Данные синтетические (см. `README.md`). Кодировка всех файлов — UTF-8, CSV — RFC 4180
> (разделитель `,`, кавычки `"`, первая строка — заголовок). **Списки внутри CSV-ячеек разделены символом `|`**;
> в JSON списки — массивы.

## games.csv / games.json — 2000 строк

| Поле | Тип | Пример | Описание и инварианты |
|---|---|---|---|
| `id` | integer | `100950` | Уникальный идентификатор игры (диапазон 100000–2999990, шаг 10, аналог appid). Первичный ключ. |
| `title` | string | `Foundry of Vesstead` | Название, уникально без учёта регистра. Может содержать `:`, `'`, цифры. |
| `developer` | string | `Red Kite Softworks` | Студия-разработчик (547 уникальных). |
| `publisher` | string | `Arclight Media` | Издатель; в ≈58% случаев совпадает с `developer` (self-published). |
| `release_date` | date `YYYY-MM-DD` | `2021-02-15` | 2010-01-01 … 2026-09-30. |
| `price_usd` | decimal(2) | `14.99` | Цена в USD, `0.00` — бесплатная игра. В CSV всегда два знака после точки. |
| `tags` | list[string] | `roguelike\|deckbuilding\|card-game` | 3–8 слагов из `tags.csv`, без повторов. Порядок — от «основных» к второстепенным, но семантики не несёт. |
| `genres` | list[string] | `Strategy\|Indie` | 1+ жанров из фиксированного списка (13 значений): Action, Adventure, Casual, Early Access, Free to Play, Indie, Massively Multiplayer, Puzzle, RPG, Racing, Simulation, Sports, Strategy. |
| `short_description` | string | `Foundry of Vesstead is a deep real-time strategy game…` | Описание на английском, ≈18–75 слов, уникально. |
| `reviews_total` | integer ≥ 0 | `345` | Число отзывов. |
| `reviews_positive_ratio` | decimal(3) \| null | `0.893` | Доля положительных отзывов, 0…1. **Пусто (CSV) / `null` (JSON), если `reviews_total = 0`.** |
| `platforms` | list[string] | `windows\|mac` | Подмножество `windows`, `mac`, `linux`; `windows` есть всегда. |
| `estimated_owners_range` | string | `20,000 .. 50,000` | Диапазон оценки числа владельцев в стиле SteamSpy. Границы: 0, 20 000, 50 000, 100 000, 200 000, 500 000, 1 000 000, 2 000 000, 5 000 000, 10 000 000, 20 000 000, 50 000 000. |

Связанные инварианты: если `price_usd = 0`, в `genres` есть `Free to Play`; тег `free-to-play` встречается только у бесплатных игр
(но не у всех бесплатных); если в `tags` есть `early-access`, в `genres` есть `Early Access`.

## tags.csv — 68 строк

| Поле | Тип | Описание |
|---|---|---|
| `slug` | string | Идентификатор тега (`procedural-generation`), уникален, используется в `games.tags` и в API. |
| `name` | string | Отображаемое имя (`Procedural Generation`). |
| `category` | enum | `genre`, `mechanic`, `theme`, `mode`, `style`, `mood`, `business`. |
| `games_count` | integer | Число игр с этим тегом (≥ 1 для каждого тега текущего датасета). |

## reviews.csv — 8883 строки

| Поле | Тип | Описание |
|---|---|---|
| `review_id` | integer | Уникальный идентификатор отзыва, 1…N. |
| `game_id` | integer | Ссылка на `games.id` (60 различных игр, 40–200 отзывов на игру). |
| `recommended` | boolean (`true`/`false`) | Рекомендует ли автор игру. |
| `text` | string | Текст отзыва на английском (1–4 предложения). Может быть в нижнем регистре, содержать префиксы вида `TL;DR:`. |
| `playtime_hours` | decimal(1) | Наигранные часы на момент отзыва. |
| `created_at` | datetime ISO 8601 UTC | `2022-06-20T17:43:41Z`; не раньше `release_date` игры. |

Число строк в `reviews.csv` для игры **не равно** `reviews_total`: это выборка (как и в реальном сборе — не более 200 на игру).

## metadata.json

Seed, дата среза (`data_cutoff`), счётчики сущностей, разделитель списков и дисклеймер о синтетичности.

## Соответствие API

Поля `games` один в один соответствуют схеме `GameDetail` в `mock-api/openapi.yaml`; `GameSummary` — то же
без `short_description` и `estimated_owners_range`. Контракт есть в пакетах бэкенда и фронтенда.
