# Известные ловушки

- `pytest` в backend печатает `StarletteDeprecationWarning`: TestClient на текущем Starlette просит пакет `httpx2` вместо `httpx`. Тест при этом зелёный. На `httpx2` не переходим, пока этого не потребует связка FastAPI и Starlette.
