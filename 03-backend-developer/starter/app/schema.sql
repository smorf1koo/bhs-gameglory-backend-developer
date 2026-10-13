-- TODO: схема каталога для SQLite (для PostgreSQL — по аналогии).
-- Применяется функцией app.db.init_schema() из import_data.py; используйте CREATE TABLE IF NOT EXISTS.
--
-- Что нужно хранить (поля — см. shared-data/schema.md):
--   * игры: id, title, developer, publisher, release_date, price_usd, short_description,
--     reviews_total, reviews_positive_ratio (может быть NULL), estimated_owners_range, genres, platforms;
--   * словарь тегов из tags.csv: slug, name, category;
--   * связь «игра — тег» (многие-ко-многим): по ней фильтруют /games?tags=... и считают /niches/{tag}/stats.
-- Подумайте о первичных и внешних ключах, NOT NULL и о том, как импорт избежит дублей.

PRAGMA foreign_keys = ON;
