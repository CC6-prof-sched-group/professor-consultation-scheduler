#!/bin/bash
set -o errexit

pip install -r requirements.txt

python prof_consult/manage.py collectstatic --no-input
python prof_consult/manage.py migrate