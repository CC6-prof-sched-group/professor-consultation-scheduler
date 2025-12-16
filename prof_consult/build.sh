#!/bin/bash
set -o errexit

pip install -r requirements.txt

python prof_consult/manage.py collectstatic --no-input
python prof_consult/manage.py migrate
python prof_consult/manage.py update_site_domain

# Configure Django Site from environment if SITE_DOMAIN is set
if [ -n "$SITE_DOMAIN" ]; then
    python prof_consult/manage.py configure_site
fi