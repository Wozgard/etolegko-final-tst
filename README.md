# Keitaro campaigns

Небольшой интерфейс к Admin API Keitaro. На первом экране — кампании с префиксом `test_shvirev_` и создание новой по имени, гео и уже существующему офферу. На втором — офферы потока: доли правятся локально и уходят в Keitaro только по кнопке «В Keitaro».

Нужны Python 3.11 или новее и Node.js 18 или новее.

## Запуск

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

В `backend/.env` вписывается `KEITARO_API_KEY`. При `KEITARO_MOCK=true` интерфейс работает на сиде и ключ для просмотра не нужен.

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Интерфейс открывается на http://127.0.0.1:5173 и ходит в API на http://localhost:8000. Другой адрес API задаётся переменной `VITE_API_URL`.

## Тесты

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

```powershell
cd frontend
npm test
```

Тесты бэкенда ходят в фейковый клиент и в трекер не обращаются.

Отдельно, уже на запущенном интерфейсе с `KEITARO_MOCK=true`, проверяется удаление оффера на стороне Keitaro. Команда из каталога `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.mocks.remove_marked_offers
```

Она снимает с потоков запущенного мока только офферы-ошибки: 401 Unauthorized, 402 Payment Required, 403 Forbidden, 404 Not Found, 405 Method Not Allowed, 408 Request Timeout, 409 Conflict, 410 Gone, 429 Too Many Requests, 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout. Греческие офферы 10–30 она не трогает. В сиде на `test_shvirev_alpha` из них лежит 404 Not Found Offer.

Сначала откройте кампанию, затем запустите команду и обновите страницу. Пропавший оффер остаётся внизу с 0% и кнопкой «Вернуть», доли остальных пересчитываются, таблица помечается изменённой, над ней текст про изменения на стороне Keitaro. В файл сида и в базу команда не пишет.

## .env

Рабочий файл — `backend/.env`, он в `.gitignore`. Образец без ключа — `backend/.env.example`.

| Переменная | Зачем |
| --- | --- |
| `KEITARO_API_KEY` | Ключ Admin API, уходит заголовком `Api-Key`. В пример не кладётся. |
| `KEITARO_ADMIN_URL` | Адрес панели трекера. |
| `KEITARO_API_URL` | База Admin API. |
| `KEITARO_DOMAIN_NAME`, `KEITARO_DOMAIN_ID` | Домен, который уже есть в Keitaro. Перед созданием кампании id сверяется. |
| `KEITARO_GROUP_NAME`, `KEITARO_GROUP_ID` | Группа кампаний. |
| `KEITARO_SOURCE_NAME`, `KEITARO_SOURCE_ID` | Источник трафика. |
| `KEITARO_MOCK` | `true` — не ходить в трекер, читать `backend/app/mocks/keitaro.json`. `false` — живой API, тогда нужен ключ. |

База SQLite создаётся сама: `sqlite:///./app.db` в каталоге `backend`.
