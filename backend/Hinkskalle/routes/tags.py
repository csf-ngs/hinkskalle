from Hinkskalle import registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import DoesNotExist, ValidationError
from flask import request, current_app

from Hinkskalle.models import Tag, Container

class TagResponseSchema(ResponseSchema):
  data = fields.Dict()

class TagUpdateSchema(RequestSchema):
  pass

@registry.handles(
  rule='/v1/tags/<string:container_id>',
  method='GET',
  response_body_schema=TagResponseSchema(),
)
def get_tags(container_id):
  try:
    container = Container.objects.get(id=container_id)
  except DoesNotExist:
    raise errors.NotFound(f"container {container_id} not found")
  
  return { 'data': container.imageTags() }

@registry.handles(
  rule='/v1/tags/<string:container_id>',
  method='POST',
  response_body_schema=TagResponseSchema(),
  authenticators=fsk_admin_auth,
)
def update_tag(container_id):
  try:
    container = Container.objects.get(id=container_id)
  except DoesNotExist:
    raise errors.NotFound(f"container {container_id} not found")

  tag = request.get_json(force=True)
  tag_name = list(tag)[0]
  try:
    new_tag = container.tag_image(tag_name, tag[tag_name])
  except DoesNotExist:
    raise errors.NotFound(f"Image {tag[tag_name]} not found for container {container_id}")
  except ValidationError:
    raise errors.NotFound(f"Invalid image id {tag[tag_name]} not found for container {container_id}")

  current_app.logger.debug(f"created tag {new_tag.name} on {new_tag.image_ref.id}")
  return { 'data': container.imageTags() }







