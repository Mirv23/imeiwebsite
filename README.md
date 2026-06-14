# Veridex — IMEI verification service

> *Every IMEI, verified in seconds.*

A mobile-first IMEI-checking website built with **Django**. Paste a 15-digit
IMEI, pick a check (blacklist, Find My / iCloud, SIM-lock, carrier, warranty…),
and get a plain-language verdict. The verification engine is mocked today but
the data model and code are structured to drop in a real provider API later
without touching the views or templates.

The brand (palette, logo, typography, voice) lives in [`brand/brand.md`](brand/brand.md)
and is codified as design tokens in [`static/css/tokens.css`](static/css/tokens.css).

---

## Local development

```bash
# 1. Create + activate a virtualenv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up the database + seed the service catalog
python manage.py migrate
python manage.py seed_services

# 4. (optional) create an admin user
python manage.py createsuperuser

# 5. Run
python manage.py runserver
```

Open http://127.0.0.1:8000 . Admin is at `/admin/`.

Locally the app uses **SQLite** automatically. No `DATABASE_URL` needed.

---

## Project structure

```
veridex/            # Django project (settings, urls, wsgi/asgi)
core/               # The app
  models.py         #   ServiceCategory, Service, Order, CheckResult
  validators.py     #   IMEI validation (length + Luhn checksum)
  services.py       #   run_lookup() — the verdict engine (mock → real API here)
  forms.py          #   OrderForm
  views.py          #   home / services / place_order / order_result
  templatetags/     #   {% icon %} SVG icon set
  management/        #  seed_services command
templates/          # base + pages (home, services, place_order, result)
static/css/         # tokens.css (the brand) + styles.css (mobile-first system)
static/js/app.js    # drawer, scroll reveals, count-up, IMEI formatting, etc.
brand/brand.md      # brand spec (colors, logo, type, voice)
```

## Wiring a real IMEI provider

The only file that needs to change is [`core/services.py`](core/services.py):
implement `run_lookup(order)` to call your provider, store the untouched
response in `CheckResult.raw_payload`, and map it into `verdict` / `headline` /
`summary` / `fields`. Views, forms, templates, and the data model stay as-is.

---

## Deploying to Vercel

Django runs on Vercel as a Python serverless function. **Important:** Vercel's
filesystem is read-only and ephemeral, so **SQLite cannot be used in
production** — you need a managed Postgres. Free options: Vercel Postgres, Neon,
Supabase.

### 1. Provision a Postgres database
Create one (e.g. on [Neon](https://neon.tech)) and copy its connection string,
which looks like `postgres://user:pass@host/dbname?sslmode=require`.

### 2. Push this repo to GitHub
```bash
git init
git add .
git commit -m "Veridex IMEI service"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 3. Import the project on Vercel
On vercel.com → **Add New → Project** → import the repo. Vercel auto-detects
[`vercel.json`](vercel.json).

### 4. Set environment variables (Project → Settings → Environment Variables)
| Variable | Value |
|---|---|
| `DATABASE_URL` | your Postgres connection string |
| `DJANGO_SECRET_KEY` | a long random string |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-project.vercel.app` (optional, after first deploy) |

> Make sure `DATABASE_URL` is available to **all environments (incl. build)** —
> the build step runs `migrate` and `seed_services` against it.

### 5. Deploy
Vercel runs [`build_files.sh`](build_files.sh) (installs deps, `collectstatic`,
`migrate`, `seed_services`) and serves the app. Static files are served from the
CDN via the `/static/*` route.

### What the config does
- `veridex/wsgi.py` exposes `app = application` for `@vercel/python`.
- `whitenoise` + `CompressedStaticFilesStorage` keep static handling
  serverless-safe (no runtime manifest dependency).
- `dj-database-url` reads `DATABASE_URL`; falls back to SQLite locally.
- `ALLOWED_HOSTS` includes `.vercel.app`; `CSRF_TRUSTED_ORIGINS` trusts the
  Vercel domain.

> Prefer an even simpler Django host? Railway, Render, and Fly.io run Django with
> persistent disks and one-command Postgres, no serverless caveats. The same
> `requirements.txt` + `DATABASE_URL` work there too.

---

## Premium animations (Magic MCP)

The **Magic MCP** server (`@21st-dev/magic`) has been added to your Claude config.
**Restart Claude Code** to activate it, then you can generate richer animated
components and drop them into `templates/` + `static/`. The current animations
(scan beam, scroll reveals, count-ups, spring buttons) are hand-built CSS/JS and
respect `prefers-reduced-motion`.
