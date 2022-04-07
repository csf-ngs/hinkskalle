FROM golang:1.13 as singularity-build-stage

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    uuid-dev \
    libseccomp-dev \
    pkg-config \
    squashfs-tools \
    cryptsetup \
    git

RUN mkdir -p ${GOPATH}/src/github.com/sylabs \
  && cd ${GOPATH}/src/github.com/sylabs \
  && git clone https://github.com/sylabs/singularity.git \
  && cd singularity \
  && git fetch --all \
  && git checkout v3.8.0 \
  && ./mconfig \
  && cd ./builddir \
  && make \
  && make install \
  && mv /usr/local/etc/singularity/singularity.conf /usr/local/etc/singularity/singularity.conf.bak \
  && sed -e 's/mount hostfs = no/mount hostfs = yes/' /usr/local/etc/singularity/singularity.conf.bak > /usr/local/etc/singularity/singularity.conf 


FROM node:lts as frontend-build-stage
WORKDIR /app
COPY frontend/package*.json yarn.lock ./
RUN yarn install
COPY ./frontend/ .
RUN JSON_STRING='window.configs = { "VUE_APP_BACKEND_URL":"%VUE_APP_BACKEND_URL%", "VUE_APP_ENABLE_REGISTER":%VUE_APP_ENABLE_REGISTER% }' \
  && sed "s@// RUNTIME_CONFIG@${JSON_STRING}@" public/index.html.tpl > public/index.html
RUN yarn build

FROM ubuntu:20.04

ENV TZ=Europe/Vienna

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends bash curl locales gosu ca-certificates tzdata \
  && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
  && sed -i -e 's/# \(en_US\.UTF-8 .*\)/\1/' /etc/locale.gen \
  && locale-gen

ENV LC_ALL en_US.UTF-8

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-dev python3-setuptools python3-distutils git \
  && pip3 install --upgrade pip

RUN echo "deb http://apt.postgresql.org/pub/repos/apt focal-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
   && apt-get install --no-install-recommends -y gnupg2 \
  && curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
  && apt-get update \
  && apt-get install -y --no-install-recommends postgresql-client libpq-dev \
  && apt-get autoremove -y gnupg2

RUN pip3 install gunicorn[gevent] \
  && pip3 uninstall -y enum34 \
  && apt-get install -y gcc \
  && pip3 install psycopg2 \
  && apt-get autoremove -y gcc


RUN useradd -d /srv/hinkskalle -m -s /bin/bash hinkskalle
RUN mkdir -p /data/db

COPY --chown=hinkskalle backend /srv/hinkskalle/backend
RUN cd /srv/hinkskalle/backend \
  && pip3 install '.[postgres]' 

WORKDIR /srv/hinkskalle

COPY conf/config.json /srv/hinkskalle/conf/

COPY --from=singularity-build-stage /usr/local/bin/*singularity* /usr/local/bin/
COPY --from=singularity-build-stage /usr/local/etc/singularity/ /usr/local/etc/singularity/
COPY --from=singularity-build-stage /usr/local/libexec/singularity/ /usr/local/libexec/singularity/
COPY --from=singularity-build-stage /usr/local/var/singularity/ /usr/local/var/singularity/

RUN mkdir -p /srv/hinkskalle/frontend/dist \
  && chown -R hinkskalle /srv/hinkskalle/frontend
COPY --chown=hinkskalle --from=frontend-build-stage /app/dist /srv/hinkskalle/frontend/dist/

COPY --chown=hinkskalle script /srv/hinkskalle/script

ENV FLASK_APP=Hinkskalle
ENV HINKSKALLE_SETTINGS=/srv/hinkskalle/conf/config.json
ENV BACKEND_URL=http://localhost:5000
ENV ENABLE_REGISTER=false
CMD [ "gosu", "hinkskalle", "./script/start.sh" ]
EXPOSE 5000
LABEL org.opencontainers.image.source https://github.com/csf-ngs/hinkskalle
