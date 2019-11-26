from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth, fsk_optional_auth
from flask_rebar import errors
from mongoengine import DoesNotExist
from flask import request, current_app, safe_join, send_file, g
from Hinkskalle.routes.images import _get_image
from Hinkskalle.models import Image, Container

import os
import os.path
import hashlib
import tempfile
import shutil

@registry.handles(
  rule='/v1/imagefile/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if image.container_ref.private:
    if not g.fsk_user:
      raise errors.Forbidden('Private image, please send token.')
    if not (g.fsk_user.is_admin or g.fsk_user.username == image.container_ref.createdBy):
      raise errors.Forbidden('Private image, access denied.')

  if not image.uploaded or not image.location:
    raise errors.NotAcceptable('Image is not uploaded yet?')
  
  if not os.path.exists(image.location):
    raise errors.InternalError(f"Image not found at {image.location}")
  Container.objects(id=image.container_ref.id).update_one(inc__downloadCount=1)
  Image.objects(id=image.id).update_one(inc__downloadCount=1)
  return send_file(image.location)
  
@registry.handles(
  rule='/v1/imagefile//<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_double_slash_annoy(*args, **kwargs):
  return pull_image(**kwargs)

@registry.handles(
  rule='/v1/imagefile/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_entity(collection_id, tagged_container_id):
  return pull_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile//<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_entity_double(collection_id, tagged_container_id):
  return pull_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile///<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_entity_triple_double_slash_annoy(collection_id, tagged_container_id):
  return pull_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)


@registry.handles(
  rule='/v1/imagefile/<string:entity_id>//<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection(entity_id, tagged_container_id):
  return pull_image(entity_id=entity_id, collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile//<string:entity_id>//<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection_double_slash_annoy(entity_id, tagged_container_id):
  return pull_image(entity_id=entity_id, collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile////<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection_default_entity_four(tagged_container_id):
  return pull_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)
  
@registry.handles(
  rule='/v1/imagefile///<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection_default_entity_triple(tagged_container_id):
  return pull_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile//<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection_default_entity_double(tagged_container_id):
  return pull_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile/<string:tagged_container_id>',
  method='GET',
  authenticators=fsk_optional_auth,
)
def pull_image_default_collection_default_entity_single(tagged_container_id):
  return pull_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile/<string:image_id>',
  method='POST',
  authenticators=fsk_auth,
)
def push_image(image_id):
  try:
    image = Image.objects.get(id=image_id)
  except DoesNotExist:
    raise errors.NotFound(f"Image {image_id} not found")

  if not image.container_ref.check_update_access(g.fsk_user):
    raise errors.Forbidden('access denied')

  outfn = safe_join(current_app.config.get('IMAGE_PATH'), '_imgs', image.make_filename())

  m = hashlib.sha256()
  tmpf = tempfile.NamedTemporaryFile(delete=False)

  current_app.logger.debug(f"starting upload of image {image_id} to {str(tmpf)}")

  read = 0
  while (True):
    chunk = request.stream.read(current_app.config.get("UPLOAD_CHUNK_SIZE", 16385))
    if len(chunk) == 0:
      break
    read = read + len(chunk)
    m.update(chunk)
    tmpf.write(chunk)
  
  current_app.logger.debug(f"calculating checksum...")
  digest = m.hexdigest()
  if image.hash != f"sha256.{digest}":
    raise errors.UnprocessableEntity(f"Image hash {image.hash} does not match: {digest}")
  tmpf.close()

  current_app.logger.debug(f"moving image to {outfn}")
  os.makedirs(os.path.dirname(outfn), exist_ok=True)
  shutil.move(tmpf.name, outfn)
  image.location=os.path.abspath(outfn)
  image.size=read
  image.uploaded=True
  image.save()
   
  image.container_ref.tag_image('latest', image.id)

  return 'Danke!'