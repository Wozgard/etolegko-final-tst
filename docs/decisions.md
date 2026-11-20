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

## 2026-11-20 — пересчёт весов

Ключ Keitaro лежит в `backend/.env` как `KEITARO_API_KEY`. Файл в `.gitignore`, в репозиторий не попадает. `Settings` читает его из этого файла, независимо от рабочей папки.

Панель трекера — `KEITARO_ADMIN_URL` (`https://tlgk.host/admin`). Вызовы Admin API — `KEITARO_API_URL` (`https://tlgk.host/admin_api/v1`), заголовок `Api-Key`.

Домен, группа и источник кампании фиксированы и лежат в `backend/.env` уже как id, не только как имена: домен `kylovoa.com` — `1813`, группа кампаний `FORTESTS` — `10332`, источник `FORTESTS` — `836`. Перед созданием кампании их всё равно сверяем со списками Keitaro: id мог измениться.

Правило живёт в `app.domain.weights.distribute_shares`. Тесты пишем до реализации.

Доли — целые проценты, сумма активных стремится к 100. Снятый оффер (`removed`) получает 0 и в дележе не участвует, даже если был запинен. Запиненный и не снятый сохраняет свой процент. Остальные делят `100 − сумма запиненных`. Весь остаток от деления достаётся первому такому офферу, а не по одному проценту нескольким. Если запиненные в сумме больше 100 — `ValueError`. Один только запиненный оффер остаётся со своим процентом, до 100 его не растягиваем.
