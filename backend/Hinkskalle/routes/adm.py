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

  
