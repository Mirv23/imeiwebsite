#!/bin/bash
# Vercel build step (runs in the @vercel/static-build container).
# Produces the /staticfiles output and prepares the production database.
# Requires DATABASE_URL to be set in the Vercel project env (build + runtime).
set -e

# Vercel's build image Python is PEP 668 "externally managed"; allow the install.
python3 -m pip install --break-system-packages -r requirements.txt

# Collect static assets into ./staticfiles (served by Vercel's CDN via routes).
python3 manage.py collectstatic --noinput --clear

# Apply schema + seed the service catalog against the production database.
python3 manage.py migrate --noinput
python3 manage.py seed_services
