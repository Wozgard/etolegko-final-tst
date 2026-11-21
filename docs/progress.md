# Прогресс

- 2026-11-19: ветка `feat/keitaro-campaigns`. Каркас backend и frontend. Приёмка: `pytest` в backend — 1 passed; `npm test` во frontend — 1 passed.
- 2026-11-20: TDD, пачка 1 — `backend/tests/test_weights.py` (16 кейсов). `pytest` красный: нет `app.domain.weights`. Реализации нет. `test_health.py` не менялся.
- 2026-11-20: `KEITARO_API_KEY` записан в `backend/.env`. `git check-ignore` подтверждает ignore. Значение в git не коммитим.
- 2026-11-20: в `backend/.env` добавлены `KEITARO_ADMIN_URL` и `KEITARO_API_URL` для `https://tlgk.host`. С этой машины TLS-рукопожатие до хоста не прошло.
- 2026-11-20: по Admin API найдены домен `kylovoa.com` (1813), группа кампаний `FORTESTS` (10332) и источник `FORTESTS` (836). Имена и id записаны в `backend/.env`.
- 2026-11-20: бэкенд `POST /campaigns`. Приёмка: `pytest tests/test_create_campaign.py tests/test_health.py` — 11 passed. `test_weights.py` по-прежнему красный.
- 2026-11-20: первый экран со списком и модалкой создания. `GET /campaigns` фильтрует префикс. `pytest` по списку, созданию и health — 12 passed. `npm test` во frontend — 3 passed. В браузере модалка показала ошибку Keitaro для несуществующего оффера, кампания не создалась.
- 2026-11-20: поле оффера стало поиском. `GET /offers?q=` и модалка. `pytest` поиска, создания, списка и health — 15 passed. `npm test` — 4 passed. В браузере запрос `188` нашёл оффер `18813`, создание не отправлял.
- 2026-11-21: поиск оффера — выпадающий список, индикатор в поле, отмена при стирании. `npm test` — 5 passed. В браузере список открывается поверх модалки, выбранный оффер остаётся в поле.
- 2026-11-21: строки списка кампаний — настоящие строки таблицы, клик открывает `/campaigns/:id`. `npm test` — 5 passed. В браузере две кампании стоят друг под другом.
- 2026-11-21: критичные тесты создания и списка зелёные. Редактор офферов описан тестами и пока красный: нет `GET /campaigns/{id}/streams` и экрана таблицы. `pytest` создания, списка, поиска и health — 16 passed. `test_campaign_offers.py` — 5 failed. `test_weights.py` по-прежнему красный. `npm test`: список 7 passed, экран офферов 4 failed.
