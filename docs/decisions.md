# Решения

## 2026-11-19 — каркас приложения

FSD не используем. Экрана два, фичи две, отдельных слоёв entities/widgets/processes это не окупает.

Бэкенд — слои FastAPI в `backend/app`: `api` (HTTP), `services` (Keitaro и сценарии), `domain` (чистые правила, в первую очередь веса), `models` (SQLAlchemy), `schemas` (Pydantic). Настройки в `config.py`, SQLite в `db.py` (`sqlite:///./app.db`). Локальная база нужна, чтобы помнить офферы, снятые в Keitaro: в интерфейсе они остаются с 0% и кнопкой Bring Back.

Фронтенд — `frontend/src`: `app` (Mantine и роутер), `pages` (список кампаний `/`, офферы `/campaigns/:id`), `features/create-campaign`, `features/edit-offers`, `shared/api` (fetch, без axios).

Библиотеки, которые берём сейчас:

- Бэкенд: FastAPI, uvicorn, SQLAlchemy 2, pydantic-settings, httpx, pytest.
- Фронтенд: Vite 5, React 18, TypeScript, react-router-dom, Mantine (`core`, `hooks`, `form`), Vitest, Testing Library, jsdom.

Mantine закрывает кнопки, таблицу, модалку и поля одной лёгкой библиотекой. Ant Design и MUI тяжелее, своего набора компонентов под три виджета не собираем.

Пока не подключаем axios, TanStack Query, zod, Redux и Tailwind. ESLint пришёл из шаблона Vite, отдельно его не выбирали.

`build/` и `*.egg-info` в `.gitignore`: это следы установки пакета, не исходники.
