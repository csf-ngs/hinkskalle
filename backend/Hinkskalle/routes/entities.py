from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
from flask import request, current_app, g
import datetime

from Hinkskalle.models import EntitySchema, Entity, User
from .util import _get_entity

class EntityResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema)

class EntityListResponseSchema(ResponseSchema):
  data = fields.Nested(EntitySchema, many=True)

class EntityCreateSchema(EntitySchema, RequestSchema):
  pass

class EntityUpdateSchema(EntitySchema, RequestSchema):
  name = fields.String(dump_only=True)

class EntityDeleteResponseSchema(ResponseSchema):
  status = fields.String()

@registry.handles(
  rule='/v1/entities',
  method='GET',
  response_body_schema=EntityListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def list_entities():
  if g.authenticated_user.is_admin:
    objs = Entity.query.all()
  else:
    objs = Entity.query.filter(or_(Entity.owner==g.authenticated_user, Entity.name=='default'))
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/entities/<string:entity_id>',
  method='GET',
  response_body_schema=EntityResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def get_entity(entity_id):
  entity = _get_entity(entity_id)
  if not entity.check_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to entity.")
  return { 'data': entity }

@registry.handles(
  rule='/v1/entities/',
  method='GET',
  response_body_schema=EntityResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def get_default_entity():
  return get_entity(entity_id='default')

@registry.handles(
  rule='/v1/entities',
  method='POST',
  request_body_schema=EntityCreateSchema(),
  response_body_schema=EntityResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def create_entity():
  body = rebar.validated_body
  current_app.logger.debug(body)
  body.pop('id', None)
  if body.get('name', '') == '':
    body['name']='default'
  
  if not g.authenticated_user.is_admin and body['name'] != g.authenticated_user.username:
    raise errors.Forbidden('You can only create an entity with your username.')
  
  owner = g.authenticated_user
  if g.authenticated_user.is_admin:
    entity_user = User.query.filter(User.username==body.get('name')).first()
    if entity_user:
      owner = entity_user

  new_entity = Entity(**body, owner=owner)

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
  authenticators=authenticator.with_scope(Scopes.user),
)
def update_entity(entity_id):
  body = rebar.validated_body
  entity = _get_entity(entity_id)

  if not entity.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to entity.")
  if not g.authenticated_user.is_admin and body.get('createdBy', None):
    if body.get('createdBy') != entity.createdBy:
      raise errors.Forbidden("Cannot change owner")

  for key in body:
    setattr(entity, key, body[key])
  entity.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': entity }

@registry.handles(
  rule='/v1/entities/<string:entity_id>',
  method='DELETE',
  response_body_schema=EntityDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
) 
def delete_entity(entity_id):
  entity = _get_entity(entity_id)

  if not entity.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to entity.")
  
  if entity.size > 0:
    raise errors.PreconditionFailed(f"Entity {entity.name} still has collections.")
  
  db.session.delete(entity)
  db.session.commit()

  return { 'status': 'ok' }
