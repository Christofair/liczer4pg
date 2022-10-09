#!/bin/bash
service nginx start
python3 -m gunicorn -w $WORKERS_NUMBER -b 127.0.0.1:5000 liczer4pg.goFlask:app
