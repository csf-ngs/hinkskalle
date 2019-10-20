from Hinkskalle import app, registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist
from flask import request

from Hinkskalle.models import ContainerSchema, Container, Entity, Collection

class ContainerResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema)

class ContainerCreateSchema(ContainerSchema, RequestSchema):
  pass


@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>',
  method='GET',
  response_body_schema=ContainerResponseSchema(),
)
def get_container(entity_id, collection_id, container_id):
  try:
    entity = Entity.objects.get(name=entity_id)
  except DoesNotExist:
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = Collection.objects.get(name=collection_id, entity_ref=entity)
  except DoesNotExist:
    raise errors.NotFound(f"collection {entity.id}/{collection_id} not found")
  try:
    container = Container.objects.get(name=container_id, collection_ref=collection)
  except DoesNotExist:
    raise errors.NotFound(f"container {entity.id}/{collection.id}/{container_id} not found")

  return { 'data': container }

@registry.handles(
  rule='/v1/containers',
  method='POST',
  request_body_schema=ContainerCreateSchema(),
  response_body_schema=ContainerResponseSchema(),
  authenticators=fsk_admin_auth,
)
def create_container():
  body = rebar.validated_body
  collection = Collection.objects.get(id=body['collection'])
  body.pop('collection')
  new_container = Container(**body)
  new_container.collection_ref=collection

  try:
    new_container.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Container {new_container.id} already exists")

  return { 'data': new_container }
