from flask_rq2 import RQ
from Hinkskalle import db
from Hinkskalle.models import Adm, AdmKeys
from rq import get_current_job
from flask import current_app
from time import sleep
from rq.job import Job
from redis import Redis
from sqlalchemy.orm.exc import NoResultFound
from .auth.ldap import LDAPUsers, _get_attr
from .auth.exceptions import UserConflict

rq = RQ()

def get_job_info(id):
  return Job.fetch(id, connection=Redis.from_url(rq.redis_url))


@rq.job
def sync_ldap():
  job = get_current_job()
  svc = LDAPUsers(app=current_app)
  svc.ldap.connect()
  ldap_users = svc.ldap.list_users()
  result = {
    'synced': [],
    'conflict': [],
    'failed': [],
  }
  for ldap_user in ldap_users:
    try:
      db_user = svc.sync_user(ldap_user)
      result['synced'].append(db_user.username)
    except UserConflict:
      result['conflict'].append(_get_attr(ldap_user.get('attributes').get('cn')))
    except:
      result['failed'].append(_get_attr(ldap_user.get('attributes').get('cn')))

  job.meta['what']=len(ldap_users)
  job.save_meta()

  try:
    update = Adm.query.get(AdmKeys.ldap_sync_results)
  except NoResultFound:
    update = Adm(key=AdmKeys.ldap_sync_results)
    db.session.add(update)
  update.val = result
  db.session.commit()
  
  return "synced"


