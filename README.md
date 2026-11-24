# КартофЪ — Django приложение

## Локална разработка

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
DJANGO_DEBUG=true .venv/bin/python manage.py runserver
```

Локалният `SECRET_KEY` се използва само при `DJANGO_DEBUG=true`. Не използвайте този режим на публичен сървър.

## PythonAnywhere / production

В конфигурацията на уеб приложението задайте променливите на средата:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY` — уникален случаен ключ, съхраняван като тайна
- `DJANGO_ALLOWED_HOSTS` — домейни, разделени със запетая, например `example.pythonanywhere.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS` — HTTPS origins, разделени със запетая
- `SQLITE_PATH` — постоянен път до SQLite файла извън директорията, която се разгръща с кода
- `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM` — ако ще се изпращат имейл известия
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` или Twilio променливите за автоматично WhatsApp изпращане

След deployment приложете миграциите и настройте PythonAnywhere static/media mappings:

```bash
python manage.py migrate
python manage.py collectstatic
python manage.py check --deploy
```

Настройте HTTPS пренасочване и HSTS само след като HTTPS е потвърдено за домейна. Използвайте постоянна, архивирана база и отделно архивирайте качените медийни файлове.

За HTTPS настройте `DJANGO_SECURE_SSL_REDIRECT=true`; след потвърждение на HTTPS може да зададете `DJANGO_HSTS_SECONDS` (например `31536000`). Включвайте `DJANGO_HSTS_INCLUDE_SUBDOMAINS=true` и `DJANGO_HSTS_PRELOAD=true` само ако всички поддомейни поддържат HTTPS и собственикът иска preload.
