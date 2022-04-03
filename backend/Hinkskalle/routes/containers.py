from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from flask import request, current_app, g
import datetime

from Hinkskalle.models import ContainerSchema, Container, Entity, Collection
from .util import _get_container

class ContainerResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema)

class ContainerListResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema, many=True)

class ContainerCreateSchema(ContainerSchema, RequestSchema):
  pass

class ContainerUpdateSchema(ContainerSchema, RequestSchema):
  name = fields.String(dump_only=True)
  collection = fields.String(dump_only=True)

class ContainerDeleteQuerySchema(RequestSchema):
  cascade = fields.Bool(required=False)

class ContainerDeleteResponseSchema(ResponseSchema):
  status = fields.String()

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>',
  method='GET',
  response_body_schema=ContainerListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def list_containers(entity_id, collection_id):
  try:
    entity = Entity.query.filter(Entity.name==entity_id).one()
  except NoResultFound:
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = entity.collections_ref.filter(Collection.name==collection_id).one()
  except NoResultFound:
    current_app.logger.debug(f"collection {entity.name}/{collection_id} not found")
    raise errors.NotFound(f"collection {entity.name}/{collection_id} not found")

  if not collection.check_access(g.authenticated_user):
    raise errors.Forbidden(f"access denied.")

  objs = collection.containers_ref.all()

  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='GET',
  response_body_schema=ContainerResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def get_container(entity_id, collection_id, container_id):
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_access(g.authenticated_user):
    raise errors.Forbidden("access denied.")

  return { 'data': container }

@registry.handles(
  rule='/v1/containers/<string:container_id>',
  method='GET',
  response_body_schema=ContainerResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def get_default_container(container_id):
  return get_container('default', 'default', container_id)



@registry.handles(
  rule='/v1/containers',
  method='POST',
  request_body_schema=ContainerCreateSchema(),
  response_body_schema=ContainerResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def create_container():
  body = rebar.validated_body
  try:
    collection = Collection.query.filter(Collection.id==body['collection']).one()
  except NoResultFound:
    raise errors.NotFound(f"collection {body['collection']} not found")

  if not collection.check_update_access(g.authenticated_user):
    raise errors.Forbidden(f"access denied.")
  body.pop('collection')
  owner = g.authenticated_user
  if g.authenticated_user.is_admin and collection.entity_ref.owner:
    owner = collection.entity_ref.owner
  with db.session.no_autoflush:
    new_container = Container(**body)
    new_container.collection_ref=collection
    new_container.owner=owner
    db.session.expire(collection)
    if collection.private:
      new_container.private = True

  try:
    db.session.add(new_container)
    db.session.commit()
  except IntegrityError as err:
    raise errors.PreconditionFailed(f"Container {new_container.id} already exists")

  return { 'data': new_container }

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='PUT',
  request_body_schema=ContainerUpdateSchema(),
  response_body_schema=ContainerResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def update_container(entity_id, collection_id, container_id):
  body = rebar.validated_body
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to container")
  if not g.authenticated_user.is_admin and body.get('createdBy', None):
    if body.get('createdBy') != container.createdBy:
      raise errors.Forbidden("Cannot change owner")
  

  for key in body:
    setattr(container, key,  body[key])
  container.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': container }

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='DELETE',
  query_string_schema=ContainerDeleteQuerySchema(),
  response_body_schema=ContainerDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def delete_container(entity_id, collection_id, container_id):
  args = rebar.validated_args
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to container")

  if container.images_ref.count() > 0 and not args.get('cascade', False):
      raise errors.PreconditionFailed(f"Container {container.name} still has images.")
    
  db.session.delete(container)
  db.session.commit()
  return { 'status': 'ok' }
