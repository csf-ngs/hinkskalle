from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth, db
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from flask import request, current_app, g
import datetime

from Hinkskalle.models import EntitySchema, Entity

class EntityResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema)

class EntityListResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema, many=True)

class EntityCreateSchema(EntitySchema, RequestSchema):
  pass

class EntityUpdateSchema(EntitySchema, RequestSchema):
  name = fields.String(dump_only=True)

@registry.handles(
  rule='/v1/entities',
  method='GET',
  response_body_schema=EntityListResponseSchema(),
  authenticators=fsk_auth,
)
def list_entities():
  if g.fsk_user.is_admin:
    objs = Entity.query.all()
  else:
    objs = Entity.query.filter(or_(Entity.owner==g.fsk_user, Entity.name=='default'))
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/entities/<string:entity_id>',
  method='GET',
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_auth,
)
def get_entity(entity_id):
  try:
    entity = Entity.query.filter(Entity.name == entity_id).one()
  except NoResultFound:
    raise errors.NotFound(f"entity {entity_id} not found")
  if not entity.check_access(g.fsk_user):
    raise errors.Forbidden("Access denied to entity.")
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
  new_entity.owner = g.fsk_user

  try:
    db.session.add(new_entity)
    db.session.commit()
  except IntegrityError as err:
    raise errors.PreconditionFailed(f"Entity {new_entity.id} already exists")

  return { 'data': new_entity }

@registry.handles(
  rule='/v1/entities/<string:entity_id>',
  method='PUT',
  request_body_schema=EntityUpdateSchema(),
  response_body_schema=EntityResponseSchema(),
  authenticators=fsk_auth,
)
def update_entity(entity_id):
  body = rebar.validated_body

  try:
    entity = Entity.query.filter(Entity.name==entity_id).one()
  except NoResultFound:
    raise errors.NotFound(f"entity {entity_id} not found")
  if not entity.check_update_access(g.fsk_user):
    raise errors.Forbidden("Access denied to entity.")

  for key in body:
    setattr(entity, key, body[key])
  entity.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': entity }

  