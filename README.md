# threads_parser

Скрапер Threads.net для Exorde. Архитектура повторяет `reddit_parser`
(workers, SeenCache, TokenBucket, batch POST в `/store_items`), но сбор
данных идёт через Playwright + cookies (Cookie Editor JSON) + proxy на
аккаунт, поскольку у Threads нет открытого read-API уровня `reddit.com/....json`.

## Структура

```
.
├── main.py                   # точка входа: конфиг, общие объекты, запуск воркеров
├── scraper/
│   ├── __init__.py
│   ├── constants.py          # пути, таймауты, логгер, константы (DOMAIN=threads.net)
│   ├── config.py             # ConfigStore (hot-reload config.yaml), load_accounts, load_cookies
│   ├── state.py               # TokenBucket, SeenCache (claim/confirm/release)
│   ├── pipeline.py           # build_payload (схема Exorde) + send_batch (/store_items)
│   ├── worker.py             # account_worker (цикл на аккаунт), заглушка v1
│   └── browser.py            # Playwright-сессия: proxy + cookies, заглушка fetch_new_posts
├── config.yaml                # тюнинг: target_rate, poll_interval, targets, batch_max_items...
├── accounts.yaml              # слоты аккаунтов: cookie_file + proxy (креды из .env) + enabled
├── cookies/account_N.json     # cookies аккаунтов (Cookie Editor export) — НЕ коммитить
├── requirements.txt
└── .env.example
```

## Статус v1

Это каркас. `scraper/browser.py:ThreadsBrowserSession.fetch_new_posts()` —
заглушка (`NotImplementedError`), потому что для реального парсинга ленты
Threads нужны:

1. Ваш `storage_state`/DOM-структура целевой страницы (профиль/тема), ИЛИ
2. HAR-файл сетевых запросов Threads (если решим переключиться на
   HTTP/GraphQL вместо DOM-парсинга).

Без этого пришлось бы придумывать селекторы и структуру ответа — то есть
писать фейковый парсинг, что запрещено правилами Exorde (никаких
фейковых id/timestamps/content).

Всё остальное — конфиг, дедуп, рейт-лимит, батчинг, сборка payload под
схему Exorde — рабочее и не зависит от того, как именно будет получен
сырой пост.

## Схема payload (Exorde)

```
{
  "content": str,              # текст поста/реплая
  "external_id": str,          # реальный id поста из Threads
  "created_at": str,           # ISO8601, реальное время публикации
  "url": str,                  # реальная ссылка на пост
  "title": str,                # обычно "" — у Threads нет заголовков постов
  "author": str,                # display name
  "username": str,              # handle без @
  "external_parent_id": str,   # "" для top-level поста, id родителя для reply
  "domain": "threads.net",
  "summary": str                 # JSON-строка (не объект!) с доп. метаданными
}
```

Правило parent_id: top-level post → `external_parent_id = ""`;
reply → `external_parent_id` = реальный id родительского поста (не автора,
не темы — именно поста, на который отвечают).

## Запуск (без Docker, для разработки)

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # заполнить STORE_ENDPOINT при необходимости
python3 main.py
```

Локальный коллектор Exorde (`store_items`) должен слушать на
`STORE_ENDPOINT` (по умолчанию `http://127.0.0.1:9000/store_items`).
Парсер никогда не шлёт напрямую на `upload.exorde.network`.

## Cookies

1. Залогинься в Threads в браузере под нужным аккаунтом.
2. Экспортируй cookies расширением Cookie Editor → Export → JSON.
3. Сохрани как `cookies/account_1.json` (и т.д. для остальных аккаунтов).
4. В `accounts.yaml` выстави этому аккаунту `enabled: true` и укажи
   `proxy_user_env`/`proxy_pass_env` — реальные значения только в `.env`.

`cookies/` в `.gitignore` — файлы с сессиями в git не попадают.

## Proxy

Обязателен для каждого аккаунта (см. `accounts.yaml`). Креды прокси —
только через переменные окружения из `.env`, в конфиге — плейсхолдеры
(имена env-переменных), не значения.

## Что нужно от вас дальше

1. Первый `cookies/account_1.json` (Cookie Editor export) для теста.
2. Прокси на аккаунт (host/port/протокол — креды положите в `.env`).
3. Список целей: usernames/URL профилей или тем, которые парсим
   (пойдёт в `config.yaml:targets`).
4. Либо доступ посмотреть DOM реальной страницы Threads (структура постов/
   реплаев), либо HAR — чтобы реализовать `browser.py:fetch_new_posts`
   без придумывания структуры.
