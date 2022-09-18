import typing
from flask.app import Flask
from flask_rq2 import RQ
from rq_scheduler.scheduler import Scheduler
from Hinkskalle import db
from rq import get_current_job
from flask import current_app
from flask_rq2.job import Job
from datetime import datetime, timezone
from sqlalchemy import func
import traceback
import time

from Hinkskalle.models.Adm import Adm, AdmKeys
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Image import Image, UploadStates
from Hinkskalle.models.User import User
from .auth.ldap import LDAPUsers, _get_attr
from .auth.exceptions import UserConflict
import os
import os.path

rq = RQ()

def setup_cron(app: Flask) -> None:
  for key in app.config.get('CRON', {}):
    if not key in adm_map:
      raise Exception(f"Invalid adm key {key} in CRON")
    app.logger.debug(f"scheduling {key}...")
    job: Job = adm_map[key].cron(app.config['CRON'][key], key)

def get_cron():
  scheduler = Scheduler(connection=rq.connection)
  jobs = scheduler.get_jobs(with_times=True)
  def to_local(dt: datetime) -> typing.Optional[datetime]:
    return dt.replace(tzinfo=timezone.utc).astimezone() if dt else None
  ret = []
  for j in jobs:
    j[0].enqueued_at=to_local(j[0].enqueued_at) # type: ignore
    ret.append((j[0], to_local(j[1]))) # type: ignore
  return ret


def get_job_info(id) -> Job:
  return Job.fetch(id, connection=rq.connection)

@rq.job
def expire_images() -> typing.Optional[str]:
  current_app.logger.debug(f"starting image expiration...")
  job: typing.Optional[Job] = get_current_job()
  if not job:
    return
  result = {
    'job': job.id,
    'started': datetime.now(tz=timezone.utc).isoformat(),
    'updated': 0,
    'space_reclaimed': 0,
  }
  job.meta['progress']='starting'
  job.save_meta()
  try:
    to_delete = Image.query.filter(Image.expiresAt < datetime.now(), Image.uploadState == UploadStates.completed)
    total_count = to_delete.count()

    for image in to_delete:
      if image.location:
        try:
          if not image.size:
            image.size = os.path.getsize(image.location)
          os.unlink(image.location)
          result['space_reclaimed'] += image.size
        except FileNotFoundError:
          current_app.logger.debug(f"Image {image.id} path {image.location} not found")
      else:
        current_app.logger.debug(f"Image {image.id} had null location")

      image.uploadState = UploadStates.broken
      db.session.commit()

      result['updated'] += 1
      job.meta['progress']=f"{result['updated']}/{total_count}"
      job.save_meta()
    _finish_job(job, result, AdmKeys.expire_images)
  except Exception as exc:
    db.session.rollback()
    current_app.logger.error(exc)
    _fail_job(job, result, AdmKeys.expire_images, exc)
    raise exc
  current_app.logger.debug(f"image expiration finished.")
  current_app.logger.debug(result)
  return f"updated {result['updated']}"

@rq.job
def update_quotas() -> typing.Optional[str]:
  current_app.logger.debug(f"starting quota check...")
  job: typing.Optional[Job] = get_current_job()
  if not job:
    return
  result = {
    'job': job.id,
    'started': datetime.now(tz=timezone.utc).isoformat(),
    'updated': 0,
    'total_space': 0,
  }
  job.meta['progress']='starting'
  job.save_meta()
  try:
    total = Entity.query.count() + User.query.count()
    for obj in Entity.query.all() + User.query.all():
      size = obj.calculate_used()
      db.session.commit()
      result['updated'] += 1
      job.meta['progress']=f"{result['updated']}/{total}"
      job.save_meta()

    subq = db.session.query(
      Image.location,
      func.max(Image.size).label('size')
    ).filter(
      Image.uploadState==UploadStates.completed
    ).group_by(
      Image.location
    ).subquery()
    row = db.session.query(func.sum(subq.c.size).label('total_size')).first()
    result['total_space'] = row.total_size

    _finish_job(job, result, AdmKeys.check_quotas)
  except Exception as exc:
    db.session.rollback()
    current_app.logger.error(exc)
    _fail_job(job, result, AdmKeys.check_quotas, exc)
    raise exc
  current_app.logger.debug(f"quota check finished.")
  current_app.logger.debug(result)
  return f"updated {result['updated']}"
  

def _finish_job(job, result, key: AdmKeys):
  result['finished']=datetime.now(tz=timezone.utc).isoformat()
  result['success']=True
  job.meta['progress']='done'
  job.meta['result']=result
  job.save_meta()
  __update_adm(key, result)

def __update_adm(key: AdmKeys, result):
  update = Adm.query.get(key)
  if not update:
    update = Adm(key=key)
    db.session.add(update)
  update.val = result
  db.session.commit()
  
def _fail_job(job: Job, result, key: AdmKeys, exc: Exception):
  result['success']=False
  job.meta['progress']='failed'
  result['exception'] = job.exc_info or "".join(traceback.format_exception(value=exc, etype=None, tb=exc.__traceback__))
  current_app.logger.error(result)
  job.save_meta()
  __update_adm(key, result)

@rq.job
def sync_ldap() -> typing.Optional[str]:
  current_app.logger.debug(f"starting ldap sync...")
  job: typing.Optional[Job] = get_current_job()
  if not job:
    return
  svc = LDAPUsers(app=current_app)
  result = {
    'job': job.id,
    'started': datetime.now(tz=timezone.utc).isoformat(),
    'synced': [],
    'conflict': [],
    'failed': [],
  }

  if not svc.enabled:
    current_app.logger.debug(f"LDAP not configured.")
    _fail_job(job, result, AdmKeys.ldap_sync_results, Exception('LDAP not configured'))
  svc.ldap.connect()

  job.meta['progress']='fetch'
  job.save_meta()
  try:
    ldap_users = svc.ldap.list_users()

    count=0
    for ldap_user in ldap_users:
      count = count + 1
      job.meta['progress']=f"{count} of {len(ldap_users)}"
      job.save_meta()
      cn = _get_attr(ldap_user.get('attributes').get('cn'))
      try:
        db_user = svc.sync_user(ldap_user)
        result['synced'].append(db_user.username)
      except UserConflict:
        db.session.rollback()
        result['conflict'].append(cn)
      except Exception as exc:
        db.session.rollback()
        current_app.logger.warn(f"sync {cn}: {exc}")
        result['failed'].append(cn)

    _finish_job(job, result, AdmKeys.ldap_sync_results)
  except Exception as exc:
    _fail_job(job, result, AdmKeys.ldap_sync_results, exc)
    raise exc
  
  current_app.logger.debug(f"ldap sync finished")
  current_app.logger.debug(result)
  return f"synced {len(result['synced'])}"


adm_map = {
  AdmKeys.ldap_sync_results.name: sync_ldap,
  AdmKeys.expire_images.name: expire_images,
  AdmKeys.check_quotas.name: update_quotas,
}