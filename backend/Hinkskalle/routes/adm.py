from flask import current_app
from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from sqlalchemy.exc import IntegrityError

from marshmallow import fields, Schema

from Hinkskalle.models.Adm import AdmSchema, Adm, AdmKeys

class AdmResponseSchema(ResponseSchema):
  data = fields.Nested(AdmSchema)

class AdmUpdateSchema(AdmSchema, RequestSchema):
  pass

class JobSchema(Schema):
  id = fields.String()
  meta = fields.Dict()
  origin = fields.String()
  get_status = fields.String(dump_to='status')
  description = fields.String()
  dependson = fields.String()
  failure_ttl = fields.Int(allow_none=True, dump_to='failureTTL')
  ttl = fields.Int(allow_none=True)
  result_ttl = fields.Int(dump_to='resultTTL')
  timeout = fields.String()
  result = fields.String(allow_none=True)
  enqueued_at = fields.DateTime(dump_to='enqueuedAt')
  started_at = fields.DateTime(allow_none=True, dump_to='startedAt')
  ended_at = fields.DateTime(allow_none=True, dump_to='endedAt')
  exc_info = fields.String(allow_none=True, dump_to='excInfo')
  func_name = fields.String(dump_to='funcName')

class JobResponseSchema(ResponseSchema):
  data = fields.Nested(JobSchema)

class LdapPingSchema(Schema):
  status = fields.String()
  error = fields.String()

class LdapStatusSchema(Schema):
  status = fields.String()
  config = fields.Dict()

class LdapPingResponseSchema(ResponseSchema):
  data = fields.Nested(LdapPingSchema)

class LdapStatusResponseSchema(ResponseSchema):
  data = fields.Nested(LdapStatusSchema)

@registry.handles(
  rule='/v1/adm/<string:key>',
  method='GET',
  response_body_schema=AdmResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def get_key(key):
  db_key: Adm = Adm.query.get(key)
  if not db_key:
    raise errors.NotFound(f"key {key} does not exist")
  
  from Hinkskalle.util.jobs import get_cron
  for j in get_cron():
    if j[0].id == f"cron-{key}":
      db_key.val['scheduled'] = j[1]

  return { 'data': db_key }

@registry.handles(
  rule='/v1/adm/<string:key>',
  method='PUT',
  request_body_schema=AdmUpdateSchema(),
  response_body_schema=AdmResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def update_key(key):
  body = rebar.validated_body

  db_key = Adm.query.get(key)
  if not db_key:
    db_key = Adm(key=key)
    db.session.add(db_key)
  
  db_key.val = body.get('val')
  try:
    db.session.commit()
  except IntegrityError:
    raise errors.BadRequest(f"Invalid key")

  return { 'data': db_key }

@registry.handles(
  rule='/v1/ldap/status',
  method='GET',
  response_body_schema=LdapStatusResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def ldap_status():
  from Hinkskalle.util.auth.ldap import LDAPUsers
  ret = {}
  try:
    ldap = LDAPUsers(app=current_app)
    if ldap.enabled:
      ret['status']='configured'
      ret['config']=ldap.config.copy()
      ret['config'].pop('BIND_PASSWORD', '')
    else:
      ret['status']='disabled'
  except:
    ret['status']='fail'
  
  return { 'data': ret }



@registry.handles(
  rule='/v1/ldap/ping',
  method='GET',
  response_body_schema=LdapPingResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def ping_ldap():
  from Hinkskalle.util.auth.ldap import LDAPUsers
  ret={}
  try:
    svc = LDAPUsers(app=current_app)
    svc.ldap.connect()
    ret['status']='ok'
  except Exception as err:
    ret['status']='failed'
    ret['error']=str(err)
  return { 'data': ret }
  
@registry.handles(
  rule='/v1/ldap/sync',
  method='POST',
  response_body_schema=JobResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin),
)
def sync_ldap():
  """deprecated, use /v1/adm/ldap_sync_results/run"""
  return start_task(AdmKeys.ldap_sync_results.name)

@registry.handles(
  rule='/v1/adm/<string:key>/run',
  method='POST',
  response_body_schema=JobResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def start_task(key):
  from Hinkskalle.util.jobs import adm_map
  if not key in adm_map:
    raise errors.NotAcceptable(f"Invalid adm key {key}")
  job = adm_map[key].queue()
  return { 'data': job }

@registry.handles(
  rule='/v1/jobs/<string:id>',
  method='GET',
  response_body_schema=JobResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def get_job(id):
  from Hinkskalle.util.jobs import get_job_info
  job = get_job_info(id)
  if not job:
    raise errors.NotFound("job id not found")
  return { 'data': job }