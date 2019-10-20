from Hinkskalle import app, registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist
from flask import request

from Hinkskalle.models import CollectionSchema, Collection, Entity

from fsk_authenticator import FskAdminAuthenticator

class CollectionResponseSchema(ResponseSchema):
  data = fields.Nested(CollectionSchema)

class CollectionCreateSchema(CollectionSchema, RequestSchema):
  pass


@registry.handles(
  rule='/v1/collections/<string:entity_id>/<string:collection_id>',
  method='GET',
  response_body_schema=CollectionResponseSchema(),
)
def get_collection(entity_id, collection_id):
  try:
    entity = Entity.objects.get(name=entity_id)
  except DoesNotExist:
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = Collection.objects.get(name=collection_id, entity_ref=entity)
  except DoesNotExist:
    raise errors.NotFound(f"collection {entity.id}/{collection_id} not found")
  return { 'data': collection }

@registry.handles(
  rule='/v1/collections',
  method='POST',
  request_body_schema=CollectionCreateSchema(),
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_admin_auth,
)
def create_collection():
  body = rebar.validated_body
  app.logger.debug(body)
  entity = Entity.objects.get(id=body['entity'])
  body.pop('entity')
  new_collection = Collection(**body)
  new_collection.entity_ref=entity

  try:
    new_collection.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Collection {new_collection.id} already exists")

  return { 'data': new_collection }
