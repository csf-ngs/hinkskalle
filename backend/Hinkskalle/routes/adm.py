from flask import current_app
from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from sqlalchemy.exc import IntegrityError

from marshmallow import fields, Schema

from Hinkskalle.models import AdmSchema, Adm

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
  failure_ttl = fields.Int(allow_none=True)
  ttl = fields.Int(allow_none=True)
  result_ttl = fields.Int()
  timeout = fields.String()
  result = fields.String(allow_none=True)
  enqueued_at = fields.String()
  started_at = fields.String(allow_none=True)
  ended_at = fields.String(allow_none=True)
  exc_info = fields.String(allow_none=True)
  func_name = fields.String()

class JobResponseSchema(ResponseSchema):
  data = fields.Nested(JobSchema)

@registry.handles(
  rule='/v1/adm/<string:key>',
  method='GET',
  response_body_schema=AdmResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def get_key(key):
  db_key = Adm.query.get(key)
  if not db_key:
    raise errors.NotFound(f"key {key} does not exist")

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
  rule='/v1/ldap/sync',
  method='POST',
  response_body_schema=JobResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin),
)
def sync_ldap():
  from Hinkskalle.util.jobs import sync_ldap
  job = sync_ldap.queue()
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