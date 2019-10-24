from Hinkskalle import registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import DoesNotExist, ValidationError
from flask import request, current_app
import os.path

from Hinkskalle.models import Tag, Container, Image

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
  # why do you have a versioned API when you change
  # the data structure and send it to the same
  # endpoint???
  if 'Tag' in tag and 'ImageID' in tag:
    tag_name = tag['Tag']
    tag_image = tag['ImageID']
  else:
    tag_name = list(tag)[0]
    tag_image = tag[tag_name]
  try:
    new_tag = container.tag_image(tag_name, tag_image)
  except DoesNotExist:
    raise errors.NotFound(f"Image {tag_image} not found for container {container_id}")
  except ValidationError:
    raise errors.NotFound(f"Invalid image id {tag_image} not found for container {container_id}")

  current_app.logger.debug(f"created tag {new_tag.name} on {new_tag.image_ref.id}")

  image=new_tag.image_ref
  if image.uploaded and os.path.exists(image.location):
    subdir = image.collectionName() if image.entityName() == 'default' else os.path.join(image.entityName(), image.collectionName())
    target = os.path.join(current_app.config["IMAGE_PATH"], subdir, f"{image.containerName()}_{new_tag.name}.sif")
    link_from = os.path.relpath(image.location, os.path.dirname(target))
    current_app.logger.debug(f"Creating symlink {link_from}->{target}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.lexists(target):
      current_app.logger.debug(f"... removing existing {target}")
      os.remove(target)
    os.symlink(link_from, target)
  else:
    current_app.logger.warning(f"Tagged image {image.id} which was not uploaded or does not exist!")

  return { 'data': container.imageTags() }







