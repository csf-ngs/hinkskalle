from flask_rq2 import RQ
from Hinkskalle import db
from Hinkskalle.models import Adm, AdmKeys
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

  result['finished']=datetime.now(tz=timezone.utc).isoformat()
  job.meta['progress']='done'
  job.meta['result']=result
  job.save_meta()

  update = Adm.query.get(AdmKeys.ldap_sync_results)
  if not update:
    update = Adm(key=AdmKeys.ldap_sync_results)
    db.session.add(update)
  update.val = result
  db.session.commit()
  
  return f"synced {len(result['synced'])}"


