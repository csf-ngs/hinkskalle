from flask_rq2 import RQ
from rq import get_current_job
from flask import current_app
from time import sleep
from rq.job import Job
from redis import Redis

rq = RQ()

def get_job_info(id):
  return Job.fetch(id, connection=Redis.from_url(rq.redis_url))


@rq.job
def sync_ldap():
  job = get_current_job()
  job.meta['what']='w00t'
  job.save_meta()
  current_app.logger.debug("sync")
  return "synced"


