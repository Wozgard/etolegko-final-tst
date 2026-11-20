# Прогресс

- 2026-11-19: ветка `feat/keitaro-campaigns`. Каркас backend и frontend. Приёмка: `pytest` в backend — 1 passed; `npm test` во frontend — 1 passed.
- 2026-11-20: TDD, пачка 1 — `backend/tests/test_weights.py` (16 кейсов). `pytest` красный: нет `app.domain.weights`. Реализации нет. `test_health.py` не менялся.
- 2026-11-20: `KEITARO_API_KEY` записан в `backend/.env`. `git check-ignore` подтверждает ignore. Значение в git не коммитим.
- 2026-11-20: в `backend/.env` добавлены `KEITARO_ADMIN_URL` и `KEITARO_API_URL` для `https://tlgk.host`. С этой машины TLS-рукопожатие до хоста не прошло.
- 2026-11-20: по Admin API найдены домен `kylovoa.com` (1813), группа кампаний `FORTESTS` (10332) и источник `FORTESTS` (836). Имена и id записаны в `backend/.env`.
