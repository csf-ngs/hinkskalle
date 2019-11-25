FROM docker.ngs.vbcf.ac.at/singularity-base as singularity

FROM docker.ngs.vbcf.ac.at/flask-base

RUN apt-get install -y jq gosu

RUN pip3 install gunicorn[gevent]

RUN useradd -d /srv/hinkskalle -m -s /bin/bash hinkskalle

COPY --chown=hinkskalle backend /srv/hinkskalle/backend
RUN cd /srv/hinkskalle/backend \
  && pip3 install -e . 

WORKDIR /srv/hinkskalle

COPY conf/config.json /srv/hinkskalle/conf/

COPY --from=singularity /usr/local/bin/*singularity* /usr/local/bin/
COPY --from=singularity /usr/local/etc/singularity/ /usr/local/etc/singularity/
COPY --from=singularity /usr/local/libexec/singularity/ /usr/local/libexec/singularity/
COPY --from=singularity /usr/local/var/singularity/ /usr/local/var/singularity/

ENV LC_ALL=en_US.utf8
ENV FLASK_APP=Hinkskalle
ENV HINKSKALLE_SETTINGS=/srv/hinkskalle/conf/config.json
CMD [ "gunicorn", "-u", "hinkskalle", "--access-logfile", "-", "--error-logfile", "-", "--chdir", "/srv/hinkskalle/backend", "-w", "4", "--worker-class", "gevent", "--bind", "0.0.0.0:5000", "wsgi:app" ]
EXPOSE 5000
