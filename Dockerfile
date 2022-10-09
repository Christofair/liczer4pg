FROM nginx:latest
RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
ENV WORKERS_NUMBER=4
RUN apt-get update  && apt-get upgrade -y
RUN    apt-get install -y python3 \
    && apt-get install -y python3-gunicorn \
    && apt-get install -y git \
    && git clone https://github.com/krystofair/liczer4pg /usr/src/liczer4pg \
    && cd /usr/src/liczer4pg && python3 setup.py install
COPY runapp.sh /
WORKDIR /
EXPOSE 80/tcp
ENTRYPOINT sh /runapp.sh
