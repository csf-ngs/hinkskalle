FROM docker.ngs.vbcf.ac.at/flask-base

RUN apt-get install -y jq gosu

RUN useradd -d /srv/hinkskalle -m -s /bin/bash hinkskalle

ARG GIT_USER
ARG GIT_PASSWORD
COPY --chown=hinkskalle backend /srv/hinkskalle/backend
RUN apt-get install -y --no-install-recommends git \
  && cd /srv/hinkskalle/backend \
  && git config --global credential.https://ngs.vbcf.ac.at.username $GIT_USER \
  && echo "#!/bin/bash\necho '$GIT_PASSWORD'" > /tmp/gitpw.sh \
  && chmod 755 /tmp/gitpw.sh \
  && GIT_ASKPASS=/tmp/gitpw.sh pip3 install -e . \
  && rm /tmp/gitpw.sh \
  && apt-get autoremove -y git

WORKDIR /srv/hinkskalle

COPY conf/config.json /srv/hinkskalle/conf/

ENV LC_ALL=en_US.utf8
ENV FLASK_APP=Hinkskalle
ENV HINKSKALLE_SETTINGS=/srv/hinkskalle/conf/config.json
RUN pip3 install gunicorn[gevent]
CMD [ "gunicorn", "-u", "hinkskalle", "--access-logfile", "-", "--error-logfile", "-", "--chdir", "/srv/hinkskalle/backend", "-w", "4", "--worker-class", "gevent", "--bind", "0.0.0.0:5000", "wsgi:app" ]
EXPOSE 5000
