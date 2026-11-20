# Известные ловушки

- `pytest` в backend печатает `StarletteDeprecationWarning`: TestClient на текущем Starlette просит пакет `httpx2` вместо `httpx`. Тест при этом зелёный. На `httpx2` не переходим, пока этого не потребует связка FastAPI и Starlette.
- `backend/tests/test_weights.py` специально красный, пока нет `app.domain.weights`. Это не повод удалять тесты или ослаблять кейсы. Зелёным его делает реализация `distribute_shares`.
