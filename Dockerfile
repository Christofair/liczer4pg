FROM nginx:latest
COPY nginx.conf /etc/nginx/nginx.conf
ENV WORKERS_NUMBER=4
RUN apt-get update  && apt-get upgrade -y
RUN    apt-get install -y python3 \
    && apt-get install -y python3-gunicorn \
    && apt-get install -y git \
    && git clone https://github.com/krystofair/liczer4pg /usr/src/liczer4pg \
    && cd /usr/src/liczer4pg && python3 setup.py install
COPY runapp.sh /runapp.sh
WORKDIR /
EXPOSE 80/tcp
ENTRYPOINT sh /runapp.sh
