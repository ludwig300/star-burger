#!/bin/bash

ROLLBAR_TOKEN=your_rollbar_token

set -Eeuo pipefail
cd /opt/star-burger/
source venv/bin/activate
git pull origin master
revision=$(git rev-parse --short HEAD)
pip install -r requirements.txt
npm ci --include=dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python3 ./manage.py collectstatic --noinput
python3 ./manage.py migrate

sudo systemctl restart gunicorn
sudo systemctl restart star-burger

http POST https://api.rollbar.com/api/1/deploy/ access_token=$ROLLBAR_TOKEN environment=production revision=$revision local_username=`whoami`

echo "Deploy succeeded"
