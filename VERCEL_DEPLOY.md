# EduOsh: Vercel + PostgreSQL deployment

The Django API is deployed as the official Vercel Python Function in
`api/index.py`. It does not run Gunicorn, `runserver`, migrations, the
Telegram polling bot, or an import on HTTP requests.

## Required Vercel environment variables

Set these separately for Preview and Production as appropriate. Do not commit
their values to GitHub.

- `SECRET_KEY`: a new, strong Django secret key
- `DATABASE_URL`: PostgreSQL URL from Vercel Marketplace / Neon
- `DEBUG=False`
- `ALLOWED_HOSTS`: the Vercel API hostname and any custom API hostname
- `FRONTEND_URL`: canonical Next.js application URL
- `CORS_ALLOWED_ORIGINS`: comma-separated allowed Next.js origins
- `CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS frontend origins
- `TELEGRAM_BOT_TOKEN`: only if API-triggered Telegram notifications are used
- `SYNC_SECRET`: if the sync endpoints are enabled

The Telegram long-polling command (`python manage.py run_bot`) must run in a
separate worker or scheduler outside Vercel Functions. Never start it from
`api/index.py`.

## One-time PostgreSQL data migration

Run the following from a trusted local shell or a deliberate one-off job after
creating an empty Neon PostgreSQL database. Never run these commands in the
Vercel Function build or request lifecycle.

```bash
export DATABASE_URL='postgresql://...'
export DEBUG=False
python manage.py migrate
python manage.py loaddata backups/local-data-20261006-110323.json
python manage.py sqlsequencereset auth authtoken core finance | python manage.py dbshell
python manage.py data_inventory
```

Before `loaddata`, inspect the PostgreSQL inventory. If it contains business
data, stop: this migration intentionally does not merge, delete, flush,
truncate, or overwrite data. Keep the source `db.sqlite3` and both backups
unchanged. The JSON fixture preserves the existing Django password hashes.

Compare the resulting inventory with the source SQLite database, including the
documented core and finance counts, before directing frontend traffic to the
new API.

## Static and media

Vercel runs `collectstatic` at build time. WhiteNoise serves only the generated
read-only static files. User uploads under `MEDIA_ROOT` are not persistent on
Vercel; see `VERCEL_MEDIA_AUDIT.md` before enabling uploads in production.
