# Известные ловушки

- `pytest` в backend печатает `StarletteDeprecationWarning`: TestClient на текущем Starlette просит пакет `httpx2` вместо `httpx`. Тест при этом зелёный. На `httpx2` не переходим, пока этого не потребует связка FastAPI и Starlette.
- Повторный `pytest` редактора падает, если в `campaign_offers` остались строки прошлой сессии. Перед каждым тестом их чистит `backend/tests/conftest.py`. Не убирай эту очистку.
