#!/usr/bin/env bash
# One-time setup: virtualenv, Python packages and the Chromium browser Playwright drives.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ needed"'
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
.venv/bin/python -m playwright install chromium
[ -f .env ] || [ -f ../.env ] || { cp .env.example .env; echo "Created .env from .env.example — fill it in."; }
.venv/bin/python -m pytest -q
echo "Setup done."
