#!/usr/bin/env bash
set -e

apt-get update
apt-get install -y \
  libpango-1.0-0 \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev

pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --noinput
