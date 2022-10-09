#!/bin/bash
python3 -m gunicorn -w $WORKERS_NUMBER -b 127.0.0.1:5000 -D liczer4pg.goFlask:app 1>/var/log/nginx/liczer.access.log 2>/var/log/nginx/liczer.error.log
nginx -g "daemon off;"
