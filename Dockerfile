FROM nginx:latest
ENV WORKERS_NUMBER=4
COPY nginx.conf /etc/nginx/nginx.conf
RUN    apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3-gunicorn \
    && apt-get install -y git \
    && git clone https://github.com/krystofair/liczer4pg /usr/src/liczer4pg \
    && cd /usr/src/liczer4pg && python3 setup.py install

WORKDIR /
EXPOSE 80/tcp
ENTRYPOINT python3 -m gunicorn -w $WORKERS_NUMBER -b 127.0.0.1:5000 liczer4pg.goFlask:app
