from flask_rq2 import RQ
from Hinkskalle import db
from Hinkskalle.models import Adm, AdmKeys
from Hinkskalle.models.Entity import Entity
from rq import get_current_job
from flask import current_app
from time import sleep
from rq.job import Job
from .auth.ldap import LDAPUsers, _get_attr
from .auth.exceptions import UserConflict
from datetime import datetime, timezone

rq = RQ()

def get_job_info(id):
  return Job.fetch(id, connection=rq.connection)


@rq.job
def update_quotas():
  job = get_current_job()
  result = {
    'job': job.id,
    'started': datetime.now(tz=timezone.utc).isoformat(),
    'updated': 0,
    'total_space': 0,
  }
  job.meta['progress']='starting'
  job.save_meta()
  total_entites = Entity.query.count()
  for entity in Entity.query.all():
    size = entity.calculate_used()
    db.session.commit()
    result['total_space'] += size
    result['updated'] += 1
    job.meta['progress']=f"{result['updated']}/{total_entites}"
    job.save_meta()
  _finish_job(job, result, AdmKeys.check_quotas)
  return f"updated {len(result['updated'])}"
  

def _finish_job(job, result, key):
  result['finished']=datetime.now(tz=timezone.utc).isoformat()
  job.meta['progress']='done'
  job.meta['result']=result
  job.save_meta()

  update = Adm.query.get(key)
  if not update:
    update = Adm(key=key)
    db.session.add(update)
  update.val = result
  db.session.commit()
  



@rq.job
def sync_ldap():
  job = get_current_job()
  svc = LDAPUsers(app=current_app)
  svc.ldap.connect()

  result = {
    'job': job.id,
    'started': datetime.now(tz=timezone.utc).isoformat(),
    'synced': [],
    'conflict': [],
    'failed': [],
  }

  job.meta['progress']='fetch'
  job.save_meta()
  ldap_users = svc.ldap.list_users()

  count=0
  for ldap_user in ldap_users:
    count = count + 1
    job.meta['progress']=f"{count} of {len(ldap_users)}"
    job.save_meta()
    try:
      db_user = svc.sync_user(ldap_user)
      result['synced'].append(db_user.username)
    except UserConflict:
      result['conflict'].append(_get_attr(ldap_user.get('attributes').get('cn')))
    except:
      result['failed'].append(_get_attr(ldap_user.get('attributes').get('cn')))

  _finish_job(job, result, AdmKeys.ldap_sync_results)
  
  return f"synced {len(result['synced'])}"


