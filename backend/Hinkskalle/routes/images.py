from Hinkskalle import app, registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist
from flask import request

from Hinkskalle.models import ImageSchema, Image, Container, Entity, Collection

class ImageResponseSchema(ResponseSchema):
  data = fields.Nested(ImageSchema)

class ImageCreateSchema(ImageSchema, RequestSchema):
  pass


@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
)
def get_image(entity_id, collection_id, tagged_container_id):
  tokens = tagged_container_id.split(":", maxsplit=1)
  container_id=tokens[0]
  if len(tokens)>1:
    tag=tokens[1]
  else:
    tag='latest'

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

  image_tags = container.imageTags()
  if not tag in image_tags:
    raise errors.NotFound(f"tag {tag} on container {entity.id}/{collection.id}/{container.id} not found")

  image = Image.objects.get(id=image_tags[tag])

  return { 'data': image }

@registry.handles(
  rule='/v1/images',
  method='POST',
  request_body_schema=ImageCreateSchema(),
  response_body_schema=ImageResponseSchema(),
  authenticators=fsk_admin_auth,
)
def create_image():
  body = rebar.validated_body
  container = Container.objects.get(id=body['container'])
  body.pop('container')

  new_image = Image(**body)
  new_image.container_ref=container

  try:
    new_image.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Image {new_image.id} already exists")

  container.tag_image('latest', new_image.id)

  return { 'data': new_image }
