# Safe Render deployment for EduOsh

This procedure preserves data. It does **not** run `flush`, `reset_db`, `DROP
DATABASE`, destructive table operations, or `loaddata` during a normal deploy.
Do not delete `db.sqlite3` or `crm_data.json` until the inventory comparison
below has been reviewed and a separate backup exists.

## 1. Identify and back up the source first

`crm_data.json` is a 23,209-record fixture, but it is not proof of a complete
production backup: it contains no `core.contract` records and no records from
the separate `finance` application. If the current CRM has contracts, finance
records, media, or records newer than this fixture, the actual source is the
existing SQLite database or current PostgreSQL database, not this fixture.

Take an immutable backup of that real source before touching Render:

```bash
# SQLite source (while the app is stopped or after copying the file safely)
cp db.sqlite3 eduosh-before-render.sqlite3
shasum -a 256 eduosh-before-render.sqlite3

# PostgreSQL source
pg_dump --format=custom --no-owner --file=eduosh-before-render.dump "$DATABASE_URL"
```

Create a count inventory from the real source and keep it next to the backup:

```bash
python manage.py data_inventory --output eduosh-before.json
```

The inventory includes users, companies, students, teachers, courses, groups,
attendance, homework tasks/submissions, payments, transactions, contracts, and
trial leads. A fixture is safe only when this source inventory is consistent
with what the fixture is intended to restore. If it is not, stop: use a tested
database-level restore/export path for the real source instead of this fixture.

For an existing PostgreSQL source, prefer database-level restore to a new Render
PostgreSQL instance. For SQLite, first create and test a controlled conversion
copy locally; do not point a production service at a partially imported target.

### Verified SQLite source migration

After `migrate` completes, run this command only in a Render Shell or one-off
Job. It is never a web-startup command. Its default is a read-only dry-run; it
requires an explicit `--apply` to write, requires PostgreSQL, refuses a target
with project records, runs in one transaction, preserves primary keys and M2M
links, maps ContentType foreign keys by natural key, and resets sequences.

```bash
python manage.py migrate_local_sqlite --source /secure/path/db.sqlite3
python manage.py migrate_local_sqlite --source /secure/path/db.sqlite3 --apply
```

Do not use it to merge, repair, or overwrite a populated target. Transfer the
SQLite file through an approved private channel; do not place it in Git. It
copies database paths only, not files beneath `MEDIA_ROOT`.

## 2. Create and configure Render services

1. Create a Render PostgreSQL instance and keep a Render backup/snapshot before
   the first migration or import.
2. Create the web service from this repository and a separate Background Worker
   for the Telegram bot. `render.yaml` supplies the safe process split but does
   not contain secrets or a database URL.
3. In both the web service and worker, set `DATABASE_URL` to the PostgreSQL
   connection string from Render and set a unique `SECRET_KEY`.
4. Set `DEBUG=False`, `FRONTEND_URL=https://eduosh1.vercel.app`,
   `CORS_ALLOWED_ORIGINS=https://eduosh1.vercel.app`, and
   `CSRF_TRUSTED_ORIGINS=https://eduosh1.vercel.app` on the web service.
5. Set `ALLOWED_HOSTS` to the actual Render hostname(s), comma-separated. Add a
   custom API hostname if one is used.
6. Set `TELEGRAM_BOT_TOKEN` only on the Background Worker. Never put it in Git
   or on the web process. One worker means exactly one polling process.

`CORS_ALLOW_ALL_ORIGINS` remains disabled. If preview domains are intentionally
needed, add their exact HTTPS origins to both CORS and CSRF variables.

## 3. Migrate, verify, and perform a one-time import only when appropriate

The web service deployment uses these commands (the Render Blueprint uses
`preDeployCommand`; on plans that do not provide pre-deploy commands, run the
migration manually in a Render Shell or one-off job before enabling/redeploying
the web service):

```bash
# Build Command
pip install -r requirements.txt && python manage.py collectstatic --noinput

# Pre-deploy / migration command
python manage.py migrate

# Start Command
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Run the migration against the target PostgreSQL database. It does not import
fixtures. Capture the initially empty target inventory before import:

```bash
python manage.py data_inventory --output eduosh-target-before-import.json
python manage.py import_initial_data --dry-run
```

Only if the source was verified to be represented by `crm_data.json`, run this
once from a Render Shell or one-off job:

```bash
python manage.py import_initial_data
python manage.py data_inventory --output eduosh-target-after-import.json
```

`import_initial_data` refuses a target containing *any* `core`, `finance`, or
token records. A later invocation logs `SKIPPED` and exits without writing, so
it cannot duplicate or overwrite production data. Compare the before-source and
after-target inventories before declaring the move successful. In particular,
zero contracts in the fixture cannot validate a source that had contracts.

Start the Telegram Background Worker separately with:

```bash
python manage.py run_bot
```

Do not use `start_with_bot.py` for the web service: Gunicorn must serve HTTP
only, while polling runs in the dedicated single worker.

## 4. Validate and rollback

Before release, run:

```bash
python manage.py makemigrations --check
python manage.py migrate --plan
python manage.py check
python manage.py check --deploy
python manage.py test
```

After deploy, validate the health endpoint, login/API requests from
`https://eduosh1.vercel.app`, and Telegram worker logs. Take a fresh Render
PostgreSQL backup after successful count comparison.

If migrations/import or verification is unsafe, stop the service and restore
the pre-change Render snapshot/`pg_dump` into a replacement database, point
`DATABASE_URL` back to that restored database, and redeploy the last known-good
commit. Never repair an uncertain transfer with `flush`, table deletion, or a
second fixture import.
