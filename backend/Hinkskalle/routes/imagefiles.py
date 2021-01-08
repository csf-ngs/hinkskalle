from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import errors, RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from flask import request, current_app, safe_join, send_file, g
from Hinkskalle.routes.images import _get_image
from Hinkskalle.models import Image, Container, ImageUploadUrl, UploadStates, UploadTypes

import os
import os.path
import hashlib
import tempfile
import shutil
from datetime import datetime, timedelta

class ImageFilePostSchema(RequestSchema):
  filesize = fields.Integer()
  sha256sum = fields.String()
  md5sum = fields.String()

class UploadImageSchema(Schema):
  uploadURL = fields.String()

class ImageFilePostResponseSchema(ResponseSchema):
  data = fields.Nested(UploadImageSchema)

class QuotaSchema(Schema):
  quotaTotal = fields.Integer()
  quotaUsage = fields.Integer()

class UploadImageCompleteSchema(Schema):
  quota = fields.Nested(QuotaSchema)
  containerUrl = fields.String()

class ImageFileCompleteResponseSchema(ResponseSchema):
  data = fields.Nested(UploadImageCompleteSchema)

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

def _get_image_id(image_id):
  try:
    image = Image.query.filter(Image.id==image_id).one()
  except NoResultFound:
    raise errors.NotFound(f"Image {image_id} not found")

  if not image.container_ref.check_update_access(g.authenticated_user):
    raise errors.Forbidden('access denied')

  if image.container_ref.readOnly:
    raise errors.NotAcceptable('container is readonly')
  return image


@registry.handles(
  rule='/v2/imagefile/<string:image_id>',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user),
  request_body_schema=ImageFilePostSchema(),
  response_body_schema=ImageFilePostResponseSchema(),
)
def push_image_v2_init(image_id):
  image = _get_image_id(image_id)
  body = rebar.validated_body

  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)
  _, tmpf = tempfile.mkstemp(dir=upload_tmp)

  upload = ImageUploadUrl(
    image_id=image.id,
    size=body.get('filesize'),
    md5sum=body.get('md5sum'),
    sha256sum=body.get('sha256sum'),
    path=tmpf,
    state=UploadStates.initialized,
    owner=g.authenticated_user,
    expiresAt=datetime.now() + timedelta(minutes=5),
    type=UploadTypes.single,
  )
  db.session.add(upload)
  db.session.commit()

  from Hinkskalle.routes import _get_service_url

  upload_url = _get_service_url()+"/v2/imagefile/_upload/"+upload.id

  return {
    'data': {
      'uploadURL': upload_url
    }
  }

@registry.handles(
  rule='/v2/imagefile/_upload/<string:upload_id>',
  method='PUT'
)
def push_image_v2_upload(upload_id):
  try:
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == upload_id).one()
  except NoResultFound:
    raise errors.NotFound(f"Invalid/unknown upload {upload_id}")
  
  if upload.state != UploadStates.initialized:
    raise errors.NotAcceptable(f"Upload {upload.id} has invalid state")
  
  upload.state=UploadStates.uploaded
  db.session.commit()
  tmpf, read = _receive_upload(open(upload.path, "wb"), f"sha256.{upload.sha256sum}")

  if read != upload.size:
    current_app.logger.error(f"Upload size mismatch {read}!={upload.size}")
    raise errors.UnprocessableEntity(f"Image size {read} does not match announced size: {upload.size}")

  upload.state=UploadStates.uploaded
  db.session.commit()
  
  return 'Danke!'


def _receive_upload(tmpf, checksum):
  m = hashlib.sha256()
  current_app.logger.debug(f"starting upload to {tmpf.name}")

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
  if checksum != f"sha256.{digest}":
    current_app.logger.error(f"upload checksum mismatch {checksum}!={digest}")
    raise errors.UnprocessableEntity(f"Image hash {checksum} does not match: {digest}")
  tmpf.close()
  return tmpf, read


@registry.handles(
  rule='/v1/imagefile/<string:image_id>',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image(image_id):
  image = _get_image_id(image_id)

  outfn = safe_join(current_app.config.get('IMAGE_PATH'), '_imgs', image.make_filename())
  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  tmpf, read = _receive_upload(tempfile.NamedTemporaryFile(delete=False, dir=upload_tmp), image.hash)

  current_app.logger.debug(f"moving image to {outfn}")
  os.makedirs(os.path.dirname(outfn), exist_ok=True)
  shutil.move(tmpf.name, outfn)
  image.location=os.path.abspath(outfn)
  image.size=read
  image.uploaded=True
  db.session.commit()

  try:
    current_app.logger.debug("checking signature(s)...")
    sigdata = image.check_signature()
    if image.signed:
      current_app.logger.debug("... signed")
    db.session.commit()
  except Exception as err:
    current_app.logger.warning(f"Image signature check failed: {err}")
   
  image.container_ref.tag_image('latest', image.id)

  return 'Danke!'