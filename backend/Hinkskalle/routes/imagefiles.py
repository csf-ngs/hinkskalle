from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth import Scopes
from flask_rebar import errors
from sqlalchemy.orm.exc import NoResultFound
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
  authenticators=authenticator.with_scope(Scopes.optional),
)
def pull_image(entity_id, collection_id, tagged_container_id):
  image = _get_image(entity_id, collection_id, tagged_container_id)
  if not image.check_access(g.authenticated_user):
    raise errors.Forbidden('Private image, access denied.')

  if not image.uploaded or not image.location:
    raise errors.NotAcceptable('Image is not uploaded yet?')
  
  if not os.path.exists(image.location):
    raise errors.InternalError(f"Image not found at {image.location}")
  container = Container.query.filter(Container.id==image.container_id).one()
  container.downloadCount += 1
  image.downloadCount += 1
  db.session.commit()

  return send_file(image.location)
  
@registry.handles(
  rule='/v1/imagefile/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.optional),
)
def pull_image_default_entity(collection_id, tagged_container_id):
  return pull_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)


@registry.handles(
  rule='/v1/imagefile/<string:tagged_container_id>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.optional),
)
def pull_image_default_collection_default_entity_single(tagged_container_id):
  return pull_image(entity_id='default', collection_id='default', tagged_container_id=tagged_container_id)

@registry.handles(
  rule='/v1/imagefile/<string:image_id>',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image(image_id):
  try:
    image = Image.query.filter(Image.id==image_id).one()
  except NoResultFound:
    raise errors.NotFound(f"Image {image_id} not found")

  if not image.container_ref.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')

  if image.container_ref.readOnly:
    raise errors.NotAcceptable('container is readonly')

  outfn = safe_join(current_app.config.get('IMAGE_PATH'), '_imgs', image.make_filename())
  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  m = hashlib.sha256()
  tmpf = tempfile.NamedTemporaryFile(delete=False, dir=upload_tmp)
  current_app.logger.debug(f"starting upload of image {image_id} to {tmpf.name}")

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
  db.session.commit()
   
  image.container_ref.tag_image('latest', image.id)

  return 'Danke!'