#!/bin/bash

ROLLBAR_TOKEN=8729612243494072bb65a777c8acee76
PROJECT_NAME=star-burger

set -Eeuo pipefail
cd /opt/star-burger/
source venv/bin/activate
git reset --hard HEAD
git pull origin master
revision=$(git rev-parse HEAD)
author=$(git --no-pager show -s --format='%an <%ae>' $revision)
comment=$(git log -1 --pretty=%B)

pip install -r requirements.txt
npm ci --include=dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python3 ./manage.py collectstatic --noinput
python3 ./manage.py migrate --noinput

sudo systemctl restart star-burger

http POST https://api.rollbar.com/api/1/deploy/ access_token=$ROLLBAR_TOKEN environment=production revision=$revision local_username=`whoami` rollbar_name=$author comment="$comment" project_name=$PROJECT_NAME

echo "Deploy succeeded"
