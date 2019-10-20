from Hinkskalle import app, registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist

from Hinkskalle.models import EntitySchema, Entity

from fsk_authenticator import FskAdminAuthenticator

class EntityResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema)

class EntityCreateSchema(EntitySchema, RequestSchema):
  pass


@registry.handles(
  rule='/v1/entities/<string:id>',
  method='GET',
  response_body_schema=EntityResponseSchema(),
)
def get_entity(id):
  try:
    entity = Entity.objects.get(id=id)
  except DoesNotExist:
    raise errors.NotFound(f"entity {id} not found")
  return { 'data': entity }

@registry.handles(
  rule='/v1/entities',
  method='POST',
  request_body_schema=EntityCreateSchema(),
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_admin_auth,
)
def create_entity():
  body = rebar.validated_body
  new_entity = Entity(**body)

  try:
    new_entity.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Entity {new_entity.id} already exists")

  return { 'data': new_entity }
