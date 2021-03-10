FROM node:lts as frontend-build-stage
WORKDIR /app
COPY frontend/package*.json ./
RUN yarn install
COPY ./frontend/ .
RUN JSON_STRING='window_configs = { "VUE_APP_BACKEND_URL":"%VUE_APP_BACKEND_URL%", "VUE_APP_ENABLE_REGISTER":%VUE_APP_ENABLE_REGISTER% }' \
  && sed "s@// RUNTIME_CONFIG@${JSON_STRING}@" public/index.html.tpl > public/index.html
RUN yarn build

FROM docker.ngs.vbcf.ac.at/singularity-base as singularity

FROM docker.ngs.vbcf.ac.at/flask-base:v3.0.0

RUN apt-get install -y jq gosu

RUN pip3 install gunicorn[gevent]

RUN useradd -d /srv/hinkskalle -m -s /bin/bash hinkskalle
RUN mkdir -p /data/db

COPY --chown=hinkskalle backend /srv/hinkskalle/backend
RUN cd /srv/hinkskalle/backend \
  && pip3 install '.[postgres]' 

WORKDIR /srv/hinkskalle

COPY conf/config.json /srv/hinkskalle/conf/

COPY --from=singularity /usr/local/bin/*singularity* /usr/local/bin/
COPY --from=singularity /usr/local/etc/singularity/ /usr/local/etc/singularity/
COPY --from=singularity /usr/local/libexec/singularity/ /usr/local/libexec/singularity/
COPY --from=singularity /usr/local/var/singularity/ /usr/local/var/singularity/

RUN mkdir -p /srv/hinkskalle/frontend/dist
COPY --from=frontend-build-stage /app/dist /srv/hinkskalle/frontend/dist/

COPY --chown=hinkskalle script /srv/hinkskalle/script

ENV LC_ALL=en_US.utf8
ENV FLASK_APP=Hinkskalle
ENV HINKSKALLE_SETTINGS=/srv/hinkskalle/conf/config.json
ENV BACKEND_URL=http://localhost:5000
ENV ENABLE_REGISTER=false
CMD [ "gosu", "hinkskalle", "./script/start.sh" ]
EXPOSE 5000
LABEL org.opencontainers.image.source https://github.com/csf-ngs/hinkskalle
