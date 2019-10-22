from Hinkskalle import registry, rebar, fsk_admin_auth
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from mongoengine import NotUniqueError, DoesNotExist
from flask import request, current_app, safe_join, send_file, g

import os
import os.path
import hashlib
import tempfile
import shutil

from Hinkskalle.models import ImageSchema, Image, Container, Entity, Collection

class ImageResponseSchema(ResponseSchema):
  data = fields.Nested(ImageSchema)

class ImageCreateSchema(ImageSchema, RequestSchema):
  pass

def _parse_tag(tagged_container_id):
  tokens = tagged_container_id.split(":", maxsplit=1)
  if len(tokens) == 1:
    tokens.append('latest')
  return tokens[0], tokens[1]

def _get_image(entity_id, collection_id, tagged_container_id):
  container_id, tag = _parse_tag(tagged_container_id)

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

  if tag.startswith('sha256.'):
    shahash=tag
    try:
      image = Image.objects.get(hash=shahash, container_ref=container)
    except DoesNotExist:
      current_app.logger.debug(f"image with hash {shahash} not found in container {container.name}")
      raise errors.NotFound(f"image with hash {shahash} not found in container {container.name}")
  else:
    image_tags = container.imageTags()
    if not tag in image_tags:
      current_app.logger.debug(f"tag {tag} on container {entity.name}/{collection.name}/{container.name} not found")
      raise errors.NotFound(f"tag {tag} on container {entity.name}/{collection.name}/{container.name} not found")

    image = Image.objects.get(id=image_tags[tag])
  return image


@registry.handles(
  rule='/v1/images/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
)
def get_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if image.uploaded and (not image.location or not os.path.exists(image.location)):
    current_app.logger.debug(f"{image.location} does not exist, resetting uploaded flag.")
    image.uploaded = False
    image.location = None
    image.save()
  return { 'data': image }

@registry.handles(
  rule='/v1/images//<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ImageResponseSchema(),
)
def get_default_image(collection_id, tagged_container_id):
  return get_image(entity_id='', collection_id=collection_id, tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/images',
  method='POST',
  request_body_schema=ImageCreateSchema(),
  response_body_schema=ImageResponseSchema(),
  authenticators=fsk_admin_auth,
)
def create_image():
  body = rebar.validated_body
  current_app.logger.debug(body)
  container = Container.objects.get(id=body['container'])
  body.pop('container')

  new_image = Image(**body)
  new_image.container_ref=container
  new_image.createdBy = g.fsk_user.username

  existing_images = [ img for img in Image.objects.filter(hash=new_image.hash) if img.container_ref != container and img.uploaded ]
  if len(existing_images) > 0:
    current_app.logger.debug(f"hash already found, re-using image location {existing_images[0].location}")
    new_image.uploaded=True
    new_image.size=existing_images[0].size
    new_image.location=existing_images[0].location

  try:
    new_image.save()
  except NotUniqueError as err:
    raise errors.PreconditionFailed(f"Image {new_image.id}/{new_image.hash} already exists")

  if new_image.uploaded:
    container.tag_image('latest', new_image.id)

  return { 'data': new_image }

@registry.handles(
  rule='/v1/imagefile/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
)
def pull_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if not image.uploaded or not image.location:
    raise errors.NotAcceptable('Image is not uploaded yet?')
  
  if not os.path.exists(image.location):
    raise errors.InternalError(f"Image not found at {image.location}")
  
  return send_file(image.location)
  
@registry.handles(
  rule='/v1/imagefile//<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
)
def pull_image_double_slash_annoy(*args, **kwargs):
  return pull_image(**kwargs)

@registry.handles(
  rule='/v1/imagefile//<string:collection_id>/<string:tagged_container_id>',
  method='GET',
)
def pull_image_default(collection_id, tagged_container_id):
  return pull_image(entity_id='', collection_id=collection_id, tagged_container_id=tagged_container_id)
  

@registry.handles(
  rule='/v1/imagefile/<string:image_id>',
  method='POST',
  authenticators=fsk_admin_auth,
)
def push_image(image_id):
  try:
    image = Image.objects.get(id=image_id)
  except DoesNotExist:
    raise errors.NotFound(f"Image {image_id} not found")

  outfn = safe_join(current_app.config.get('IMAGE_PATH'), '_imgs', image.make_filename())

  m = hashlib.sha256()
  tmpf = tempfile.NamedTemporaryFile(delete=False)
  read = 0
  while (True):
    chunk = request.stream.read(curent_app.config.get("UPLOAD_CHUNK_SIZE", 16385))
    if len(chunk) == 0:
      break
    read = read + len(chunk)
    m.update(chunk)
    tmpf.write(chunk)
  
  digest = m.hexdigest()
  if image.hash != f"sha256.{digest}":
    raise errors.UnprocessableEntity("Image hash {image.hash} does not match: {digest}")
  tmpf.close()

  os.makedirs(os.path.dirname(outfn), exist_ok=True)
  shutil.move(tmpf.name, outfn)
  image.location=os.path.abspath(outfn)
  image.size=read
  image.uploaded=True
  image.save()

  image.container_ref.tag_image('latest', image.id)

  return 'Danke!'