from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist, ValidationError
from mongoengine.queryset.visitor import Q
from flask import request, current_app, g
import datetime

from Hinkskalle.models import ContainerSchema, Container, Entity, Collection

class ContainerResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema)

class ContainerListResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema, many=True)

class ContainerCreateSchema(ContainerSchema, RequestSchema):
  pass

class ContainerUpdateSchema(ContainerSchema, RequestSchema):
  name = fields.String(dump_only=True)
  collection = fields.String(dump_only=True)

def _get_container(entity_id, collection_id, container_id):
  try:
    entity = Entity.objects.get(name=entity_id)
  except DoesNotExist:
    current_app.logger.debug(f"entity {entity_id} not found")
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = Collection.objects.get(name=collection_id, entity_ref=entity)
  except DoesNotExist:
    current_app.logger.debug(f"collection {entity.name}/{collection_id} not found")
    raise errors.NotFound(f"collection {entity.name}/{collection_id} not found")
  try:
    container = Container.objects.get(name=container_id, collection_ref=collection)
  except DoesNotExist:
    current_app.logger.debug(f"container {entity.name}/{collection.name}/{container_id} not found")
    raise errors.NotFound(f"container {entity.name}/{collection.name}/{container_id} not found")
  return container

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>',
  method='GET',
  response_body_schema=ContainerListResponseSchema(),
  authenticators=fsk_auth,
)
def list_containers(entity_id, collection_id):
  try:
    entity = Entity.objects.get(name=entity_id)
  except DoesNotExist:
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = Collection.objects.get(name=collection_id, entity_ref=entity)
  except DoesNotExist:
    current_app.logger.debug(f"collection {entity.name}/{collection_id} not found")
    raise errors.NotFound(f"collection {entity.name}/{collection_id} not found")

  if not collection.check_access(g.fsk_user):
    raise errors.Forbidden(f"access denied.")

  if g.fsk_user.is_admin:
    objs = Container.objects(collection_ref=collection)
  else:
    objs = Container.objects(Q(collection_ref=collection) & Q(createdBy=g.fsk_user.username))

  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='GET',
  response_body_schema=ContainerResponseSchema(),
  authenticators=fsk_auth,
)
def get_container(entity_id, collection_id, container_id):
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_access(g.fsk_user):
    raise errors.Forbidden("access denied.")

  return { 'data': container }

@registry.handles(
  rule='/v1/containers/<string:container_id>',
  method='GET',
  response_body_schema=ContainerResponseSchema(),
  authenticators=fsk_auth,
)
def get_default_container(container_id):
  return get_container('default', 'default', container_id)



@registry.handles(
  rule='/v1/containers',
  method='POST',
  request_body_schema=ContainerCreateSchema(),
  response_body_schema=ContainerResponseSchema(),
  authenticators=fsk_auth,
)
def create_container():
  body = rebar.validated_body
  try:
    collection = Collection.objects.get(id=body['collection'])
  except ValidationError as err:
    raise errors.InternalError(str(err))
  except DoesNotExist:
    raise errors.NotFound(f"collection {body['collection']} not found")

  if not collection.check_update_access(g.fsk_user):
    raise errors.Forbidden(f"access denied.")
  body.pop('collection')
  new_container = Container(**body)
  new_container.collection_ref=collection
  new_container.createdBy=g.fsk_user.username
  if collection.private:
    new_container.private = True

  try:
    new_container.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Container {new_container.id} already exists")

  return { 'data': new_container }

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='PUT',
  request_body_schema=ContainerUpdateSchema(),
  response_body_schema=ContainerResponseSchema(),
  authenticators=fsk_auth,
)
def update_container(entity_id, collection_id, container_id):
  body = rebar.validated_body
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_update_access(g.fsk_user):
    raise errors.Forbidden("Access denied to container")

  for key in body:
    setattr(container, key,  body[key])
  container.updatedAt = datetime.datetime.now()
  container.save()

  return { 'data': container }
