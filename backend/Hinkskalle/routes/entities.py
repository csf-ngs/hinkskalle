from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist
from mongoengine.queryset.visitor import Q
from flask import request, current_app, g

from Hinkskalle.models import EntitySchema, Entity

class EntityResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema)

class EntityListResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema, many=True)

class EntityCreateSchema(EntitySchema, RequestSchema):
  pass

@registry.handles(
  rule='/v1/entities',
  method='GET',
  response_body_schema=EntityListResponseSchema(),
  authenticators=fsk_auth,
)
def list_entities():
  if g.fsk_user.is_admin:
    objs = Entity.objects()
  else:
    objs = Entity.objects(Q(createdBy=g.fsk_user.username) | Q(name='default'))
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/entities/<string:entity_id>',
  method='GET',
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_auth,
)
def get_entity(entity_id):
  if not g.fsk_user.is_admin:
    if entity_id != 'default' and entity_id != g.fsk_user.username:
      raise errors.Forbidden('Can only access default or own entity')
  try:
    entity = Entity.objects.get(name=entity_id)
  except DoesNotExist:
    raise errors.NotFound(f"entity {entity_id} not found")
  return { 'data': entity }

@registry.handles(
  rule='/v1/entities/',
  method='GET',
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_auth,
)
def get_default_entity():
  return get_entity(entity_id='default')

@registry.handles(
  rule='/v1/entities',
  method='POST',
  request_body_schema=EntityCreateSchema(),
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_auth,
)
def create_entity():
  body = rebar.validated_body
  current_app.logger.debug(body)
  body.pop('id', None)
  if body.get('name', '') == '':
    body['name']='default'
  
  if not g.fsk_user.is_admin and body['name'] != g.fsk_user.username:
    raise errors.Forbidden('You can only create an entity with your username.')

  new_entity = Entity(**body)
  new_entity.createdBy = g.fsk_user.username

  try:
    new_entity.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Entity {new_entity.id} already exists")

  return { 'data': new_entity }
