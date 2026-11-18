# Пульс — цифровой деканат

[![Backend CI](https://github.com/Chernov2312/StudKab/actions/workflows/backend.yml/badge.svg?branch=main)](https://github.com/Chernov2312/StudKab/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/Chernov2312/StudKab/actions/workflows/frontend.yml/badge.svg?branch=main)](https://github.com/Chernov2312/StudKab/actions/workflows/frontend.yml)
[![Compose and Playwright](https://github.com/Chernov2312/StudKab/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Chernov2312/StudKab/actions/workflows/ci.yml)
[![Secret scan](https://github.com/Chernov2312/StudKab/actions/workflows/secret-scan.yml/badge.svg?branch=main)](https://github.com/Chernov2312/StudKab/actions/workflows/secret-scan.yml)

Конкурсный прототип. Неофициальный сервис. Все данные вымышлены.

В кабинете есть «Мой день», профиль, расписание с переносами и отменами, оценки, сессия, заявки с историей и уведомления. Два демонстрационных аккаунта видят разные учебные данные.

## Локальный запуск

Нужны Docker Engine и Docker Compose v2. В Windows запустите Docker Desktop с Linux-контейнерами.

1. Скопируйте `.env.example` в `.env`.
2. Заполните `POSTGRES_PASSWORD` случайным значением из латинских букв и цифр, например 32-символьным hex. Задайте отдельные пароли для `demo.alina` и `demo.mark` в переменных `DEMO_ALINA_PASSWORD` и `DEMO_MARK_PASSWORD`.
3. Из корня проекта запустите:

```sh
docker compose up --build -d --wait
docker compose run --rm seed
```

Откройте [локальный кабинет](http://localhost:8080). Для входа используются `demo.alina` и `demo.mark` с выбранными вами паролями. Если меняете адрес кабинета, задайте в `.env` точный `APP_ORIGIN` с портом и без завершающего слеша. Порт прокси по умолчанию опубликован на loopback.

Compose проверяет готовность PostgreSQL, применяет Alembic-миграции отдельным сервисом, затем запускает API и Caddy. Seed работает отдельной командой, создаёт новые демозаписи идемпотентно и сохраняет данные и пароли уже созданных аккаунтов. Даты учебных записей привязываются к московскому дню первого наполнения. `docker compose down` останавливает сервисы с сохранением данных.

- Готовность приложения и БД. [Health ready](http://localhost:8080/api/v1/health/ready)
- Описание API. [OpenAPI](http://localhost:8080/api/openapi.json)
- Границы слоёв и маршруты. [Архитектура](docs/architecture.md)
- Таблицы, связи и индексы. [ER-диаграмма](docs/database-erd.md)

## Проверки

Четыре workflow запускаются на `push` и `pull_request`. Для защиты `main` назначьте обязательными проверки `backend`, `frontend`, `compose-and-browser` и `secret-scan` в правилах ветки GitHub. Бейджи показывают результаты запусков на `main`.

Из `backend/` с Python 3.12+, uv и работающим Docker:

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest -q --cov --cov-report=term-missing --cov-report=html
```

Интеграционные тесты создают одноразовую PostgreSQL через Testcontainers и применяют штатную миграцию. В `tests/integration/` каждому роутеру соответствует отдельный файл с контрактными проверками и проверками доступа. Например, `uv run pytest -q tests/integration/test_dashboard.py` запускает тесты главной. Для проверок без Docker запустите `uv run pytest -q -m "not integration"`.

Из `frontend/` с Node.js 22.13+ (LTS):

```sh
npm ci
npm run lint
npm run audit
npm run typecheck
npm test
npm run test:coverage
npm run build
npx playwright install chromium
npm run test:e2e
```

CI требует покрытие строк не ниже 80% отдельно для Python-приложения и исходников React. Для frontend порог 80% применяется к строкам, инструкциям, функциям и ветвям в Vitest. Локальные HTML-отчёты находятся в `backend/htmlcov/` и `frontend/coverage/`. CI сохраняет оба отчёта как артефакты. Playwright проверяет интеграцию на работающем приложении и выполняет аудит доступности axe по правилам WCAG 2.1 A/AA. CI сохраняет браузерный отчёт в артефакте `playwright-report`.

Playwright использует запущенный кабинет, `PULS_BASE_URL` (по умолчанию `http://localhost:8080`) и оба демопароля из окружения процесса. Для прогона наполните одноразовую демобазу в текущий день. Сценарии проверяют перенос на сегодня, отправляют заявки и меняют прочтение уведомлений. Для установленного Microsoft Edge можно задать `PULS_BROWSER_CHANNEL=msedge`. Для локальной разработки UI запустите `npm run dev` с `APP_ORIGIN=http://127.0.0.1:5173` у API. Vite проксирует запросы к `http://127.0.0.1:8080`, адрес можно задать через `PULS_API_TARGET`.

## Эксплуатация

После согласования хостинга и домена задайте `PULS_DOMAIN` без схемы, обеспечьте открытые 80/443 и корректный DNS. В production включён HTTPS, Caddy сохраняет сертификаты в отдельном томе. PostgreSQL и API доступны внутри сети Compose.

```sh
docker compose -f compose.yaml -f compose.prod.yaml up --build -d --wait
docker compose -f compose.yaml -f compose.prod.yaml run --rm seed
```

Храните окружение на хостинге с ограниченными правами. Перед публикацией сохраните резервную копию в Linux:

```sh
docker compose -f compose.yaml -f compose.prod.yaml exec -T db pg_dump -U puls -d puls -Fc > puls.dump
```

Проверьте восстановление командой `pg_restore --exit-on-error --dbname=puls_restore_check puls.dump` в отдельной тестовой PostgreSQL, предварительно создав там пустую БД `puls_restore_check`. После запуска откройте публичный HTTPS-адрес с телефона через сеть российского оператора без VPN, проверьте сертификат и пройдите сценарий обоих аккаунтов. Зафиксируйте дату, способ проверки и результаты без скриншотов со значениями паролей.

- [Продуктовые требования и контракт HTTP/JSON](Task.md)
- [Инструкции агентам](Agents.md)
- [Безопасность и откат](docs/security.md)
- [Сценарий показа](docs/demo-script.md)
- [Журнал работы с ИИ](docs/ai-process.md)
- [PDF процесса разработки](docs/ai-process.pdf)
- [Исходный репозиторий](https://github.com/Chernov2312/StudKab)
