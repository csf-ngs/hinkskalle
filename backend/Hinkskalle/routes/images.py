from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import request, current_app, safe_join, send_file, g
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

import os
import os.path
import subprocess
import json
import datetime

from Hinkskalle.models import ImageSchema, Image, Container, Entity, Collection

class ImageResponseSchema(ResponseSchema):
  data = fields.Nested(ImageSchema)

class ImageListResponseSchema(ResponseSchema):
  data = fields.Nested(ImageSchema, many=True)

class ImageCreateSchema(ImageSchema, RequestSchema):
  pass

class ImageUpdateSchema(ImageSchema, RequestSchema):
  hash = fields.String(dump_only=True)
  blob = fields.String(dump_only=True)
  uploaded = fields.String(dump_only=True)
  container = fields.String(dump_only=True)

class TagDataSchema(Schema):
  tags = fields.List(fields.String())

class ImageTagUpdateSchema(TagDataSchema, RequestSchema):
  pass

class ImageTagResponseSchema(ResponseSchema):
  data = fields.Nested(TagDataSchema)

class ImageInspectSchema(Schema):
  attributes = fields.Dict()
  type = fields.String()

class ImageInspectResponseSchema(ResponseSchema):
  data = fields.Nested(ImageInspectSchema)

class ImageDeleteResponseSchema(ResponseSchema):
  status = fields.String()

def _parse_tag(tagged_container_id):
  tokens = tagged_container_id.split(":", maxsplit=1)
  if len(tokens) == 1:
    tokens.append('latest')
  return tokens[0], tokens[1]

def _get_container(entity_id, collection_id, container_id):
  try:
    entity = Entity.query.filter(Entity.name==entity_id).one()
  except NoResultFound:
    current_app.logger.debug(f"entity {entity_id} not found")
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = entity.collections_ref.filter(Collection.name==collection_id).one()
  except NoResultFound:
    current_app.logger.debug(f"collection {entity.name}/{collection_id} not found")
    raise errors.NotFound(f"collection {entity.name}/{collection_id} not found")
  try:
    container = collection.containers_ref.filter(Container.name==container_id).one()
  except NoResultFound:
    current_app.logger.debug(f"container {entity.name}/{collection.name}/{container_id} not found")
    raise errors.NotFound(f"container {entity.name}/{collection.name}/{container_id} not found")
  return container

def _get_image(entity_id, collection_id, tagged_container_id):
  container_id, tag = _parse_tag(tagged_container_id)
  container = _get_container(entity_id, collection_id, container_id)

  if tag.startswith('sha256.'):
    shahash=tag
    try:
      image = container.images_ref.filter(Image.hash==shahash).one()
    except NoResultFound:
      current_app.logger.debug(f"image with hash {shahash} not found in container {container.name}")
      raise errors.NotFound(f"image with hash {shahash} not found in container {container.name}")
  else:
    image_tags = container.imageTags()
    if not tag in image_tags:
      current_app.logger.debug(f"tag {tag} on container {container.entityName}/{container.collectionName}/{container.name} not found")
      raise errors.NotFound(f"tag {tag} on container {container.entityName}/{container.collectionName}/{container.name} not found")

    image = Image.query.get(image_tags[tag])
  return image


@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>/images',
  method='GET',
  response_body_schema=ImageListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def list_images(entity_id, collection_id, container_id):
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  
  return { 'data': list(container.images_ref) }

@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.optional),
)
def get_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if not image.check_access(g.authenticated_user):
      raise errors.Forbidden('Private image, access denied.')

  if image.uploaded and (not image.location or not os.path.exists(image.location)):
    current_app.logger.debug(f"{image.location} does not exist, resetting uploaded flag.")
    image.uploaded = False
    image.location = None
    db.session.commit()
  return { 'data': image }

@registry.handles(
  rule='/v1/images/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.optional),
)
def get_image_default_entity_single(collection_id, tagged_container_id):
  return get_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/images/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.optional),
)
def get_image_default_entity_default_collection_single(tagged_container_id):
  return get_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/images',
  method='POST',
  request_body_schema=ImageCreateSchema(),
  response_body_schema=ImageResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def create_image():
  body = rebar.validated_body
  current_app.logger.debug(body)
  container = Container.query.get(body['container'])
  if not container:
    raise errors.NotFound(f"container {body['container']} not found")
  body.pop('container')
  if not container.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  if container.readOnly:
    raise errors.NotAcceptable('container is readonly')

  new_image = Image(**body)
  new_image.container_ref=container
  new_image.owner = g.authenticated_user

  # the db session autoflushes when running the query below
  # so we have to add here and catch any IntegrityError exceptions. 
  try:
    db.session.add(new_image)
    db.session.commit()
  except IntegrityError as err:
    raise errors.PreconditionFailed(f"Image {new_image.id}/{new_image.hash} already exists")

  # this will flush the session; if the image is not unique it would crash unless we try to insert before
  existing_images = [ img for img in Image.query.filter(Image.hash==new_image.hash).all() if img.container_id != container.id and img.uploaded ]
  if len(existing_images) > 0:
    current_app.logger.debug(f"hash already found, re-using image location {existing_images[0].location}")
    new_image.uploaded=True
    new_image.size=existing_images[0].size
    new_image.location=existing_images[0].location
    db.session.commit()

  if new_image.uploaded:
    container.tag_image('latest', new_image.id)

  return { 'data': new_image }

@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>/tags',
  method='PUT',
  request_body_schema=ImageTagUpdateSchema(),
  response_body_schema=ImageTagResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def update_image_tags(entity_id, collection_id, tagged_container_id):
  body = rebar.validated_body
  image = _get_image(entity_id, collection_id, tagged_container_id)

  if not image.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  
  existing = image.tags()
  for tag in body.get('tags', []):
    current_app.logger.debug(f"image {image.id} add tag {tag}")
    image.container_ref.tag_image(tag, image.id)
    existing = [ t for t in existing if t != tag ] 
  
  for toRemove in existing:
    current_app.logger.debug(f"image {image.id} remove tag {toRemove}")
    for tag in image.tags_ref:
      if tag.name == toRemove:
        db.session.delete(tag)
  
  db.session.commit()
  return { 'data': { 'tags': image.tags() }}

@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='PUT',
  request_body_schema=ImageUpdateSchema(),
  response_body_schema=ImageResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def update_image(entity_id, collection_id, tagged_container_id):
  body = rebar.validated_body
  image = _get_image(entity_id, collection_id, tagged_container_id)

  if not image.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')

  for key in body:
    setattr(image, key, body[key])
  image.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': image }

@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='DELETE',
  response_body_schema=ImageDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def delete_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if not image.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  db.session.delete(image)
  db.session.commit()
  if image.uploaded and image.location and os.path.exists(image.location):
    os.remove(image.location)
  return { 'status': 'ok' }


@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>/inspect',
  method='GET',
  response_body_schema=ImageInspectResponseSchema(),
)
def inspect_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if not image.uploaded or not image.location:
    raise errors.PreconditionFailed(f"Image is not uploaded yet.")
  if not os.path.exists(image.location):
    raise errors.InternalError(f"Image file at {image.location} does not exist")

  # currently using siftool to extract definition file only
  # "singularity inspect" needs to actually spin up the container
  # and works only when we're launched in privileged mode (or bareback)
  # tags are stored in the actual container file system (squashfs) -
  # metadata partitions are a thing of the future!
  inspect = subprocess.run(["singularity", "sif", "dump", "1", image.location], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if not inspect.returncode == 0:
    raise errors.InternalError(f"{inspect.args} failed: {inspect.stderr}")
  
  return { 'data': { 'attributes': { 'deffile': inspect.stdout }} }