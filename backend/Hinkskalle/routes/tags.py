from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth, db
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask import request, current_app, g
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
  authenticators=fsk_auth,
)
def get_tags(container_id):
  try:
    container = Container.query.filter(Container.id==container_id).one()
  except NoResultFound:
    raise errors.NotFound(f"container {container_id} not found")
  if not container.check_access(g.fsk_user):
    raise errors.Forbidden(f"access denied.")
  
  return { 'data': container.imageTags() }

@registry.handles(
  rule='/v1/tags/<string:container_id>',
  method='POST',
  response_body_schema=TagResponseSchema(),
  authenticators=fsk_auth,
)
def update_tag(container_id):
  try:
    container = Container.query.filter(Container.id==container_id).one()
  except NoResultFound:
    raise errors.NotFound(f"container {container_id} not found")
  if not container.check_access(g.fsk_user):
    raise errors.Forbidden('access denied.')

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
  except NoResultFound:
    raise errors.NotFound(f"Image {tag_image} not found for container {container_id}")
  except IntegrityError:
    raise errors.NotFound(f"Invalid image id {tag_image} not found for container {container_id}")

  current_app.logger.debug(f"created tag {new_tag.name} on {new_tag.image_ref.id}")

  image=new_tag.image_ref
  if image.uploaded and os.path.exists(image.location):
    subdir = image.collectionName() if image.entityName() == 'default' else os.path.join(image.entityName(), image.collectionName())
    target = os.path.join(current_app.config["IMAGE_PATH"], subdir, f"{image.containerName()}_{new_tag.name}.sif")
    current_app.logger.debug(f"Creating link {image.location}->{target}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.lexists(target):
      current_app.logger.debug(f"... removing existing {target}")
      os.remove(target)
    os.link(image.location, target)
  else:
    current_app.logger.warning(f"Tagged image {image.id} which was not uploaded or does not exist!")

  return { 'data': container.imageTags() }







