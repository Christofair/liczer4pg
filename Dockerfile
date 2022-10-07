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
CMD ["sleep", "360d"]
# ENTRYPOINT gunicorn -w $WORKERS_NUMBER 'liczer4pg.goFlask:app' -p 5000
