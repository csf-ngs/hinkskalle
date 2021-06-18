from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import errors, RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from flask import request, current_app, safe_join, send_file, g, make_response
from typing import IO, Tuple
from .images import _get_image
from .util import _get_service_url
from Hinkskalle.models import Image, Container, ImageUploadUrl, UploadStates, UploadTypes

import os
import os.path
import hashlib
import tempfile
import shutil
import math
from datetime import datetime, timedelta

class PullQuerySchema(RequestSchema):
  arch = fields.String(required=False)

class ImageFilePostSchema(RequestSchema):
  filesize = fields.Integer()
  sha256sum = fields.String()
  md5sum = fields.String(required=False)

class MultiImageFilePostSchema(RequestSchema):
  filesize = fields.Integer()

class MultiImageFilePartSchema(RequestSchema):
  partSize = fields.Integer()
  uploadID = fields.String()
  partNumber = fields.Integer()
  sha256sum = fields.String()

class UploadImageSchema(Schema):
  uploadURL = fields.String()

class UploadImagePartSchema(Schema):
  presignedURL = fields.String()

class MultiUploadImageSchema(Schema):
  uploadID = fields.String()
  partSize = fields.Integer()
  totalParts = fields.Integer()
  options = fields.Dict()

class ImageFilePostResponseSchema(ResponseSchema):
  data = fields.Nested(UploadImageSchema)

class ImageFilePostPartResponseSchema(ResponseSchema):
  data = fields.Nested(UploadImagePartSchema)

class MultiImageFilePostResponseSchema(ResponseSchema):
  data = fields.Nested(MultiUploadImageSchema)

class MultiUploadImagePartSchema(Schema):
  presignedURL = fields.String()

class MultiImageFilePartResponseSchema(ResponseSchema):
  data = fields.Nested(MultiUploadImagePartSchema)

class MultiImageUploadCompletedPartsSchema(Schema):
  partNumber = fields.Integer()
  token = fields.String()

class MultiUploadImageCompleteRequest(RequestSchema):
  uploadID = fields.String()
  completedParts = fields.Nested(MultiImageUploadCompletedPartsSchema, many=True)

class MultiUploadImageAbortRequest(RequestSchema):
  uploadID = fields.String()

class QuotaSchema(Schema):
  quotaTotal = fields.Integer()
  quotaUsage = fields.Integer()

class UploadImageCompleteRequest(RequestSchema):
  pass

class UploadImageCompleteSchema(Schema):
  quota = fields.Nested(QuotaSchema)
  containerUrl = fields.String()

class ImageFileCompleteResponseSchema(ResponseSchema):
  data = fields.Nested(UploadImageCompleteSchema)

@registry.handles(
  rule='/v1/imagefile/<string:entity_id>/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  query_string_schema=PullQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.optional),
)
def pull_image(entity_id, collection_id, tagged_container_id):
  args = rebar.validated_args
  image = _get_image(entity_id, collection_id, tagged_container_id, arch=args.get('arch', None))
  if not image.check_access(g.authenticated_user):
    raise errors.Forbidden('Private image, access denied.')

  if not image.uploaded or not image.location:
    raise errors.NotAcceptable('Image is not uploaded yet?')
  
  if image.media_type != Image.singularity_media_type:
    current_app.logger.debug(f"attempting to pull {image.media_type} via library api")
    raise errors.NotAcceptable(f"Not a singularity image")
  
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
  query_string_schema=PullQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.optional),
)
def pull_image_default_entity(collection_id, tagged_container_id):
  return pull_image(entity_id='default', collection_id=collection_id, tagged_container_id=tagged_container_id)


@registry.handles(
  rule='/v1/imagefile/<string:tagged_container_id>',
  method='GET',
  query_string_schema=PullQuerySchema(),
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

  upload_tmp = os.path.join(current_app.config['IMAGE_PATH'], '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  with tempfile.NamedTemporaryFile(delete=False) as tmpf:
    upload = ImageUploadUrl(
      image_id=image.id,
      size=body.get('filesize'),
      md5sum=body.get('md5sum'),
      sha256sum=body.get('sha256sum'),
      path=tmpf.name,
      state=UploadStates.initialized,
      owner=g.authenticated_user,
      type=UploadTypes.single,
    )
  db.session.add(upload)
  db.session.commit()

  upload_url = _get_service_url()+"/v2/imagefile/_upload/"+upload.id

  return {
    'data': {
      'uploadURL': upload_url
    }
  }

@registry.handles(
  rule='/v2/imagefile/<string:image_id>/_multipart',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user),
  request_body_schema=MultiImageFilePostSchema(),
  response_body_schema=MultiImageFilePostResponseSchema(),
)
def push_image_v2_multi_init(image_id):
  image = _get_image_id(image_id)
  body = rebar.validated_body

  upload_tmp = os.path.join(current_app.config['IMAGE_PATH'], '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)
  tmpd = tempfile.mkdtemp(dir=upload_tmp)

  part_size = current_app.config.get('MULTIPART_UPLOAD_CHUNK')
  part_count = math.ceil(body.get('filesize')/part_size)

  upload = ImageUploadUrl(
    image_id=image.id,
    size=body.get('filesize'),
    path=tmpd,
    totalParts=part_count,
    state=UploadStates.initialized,
    owner=g.authenticated_user,
    type=UploadTypes.multipart,
  )
  db.session.add(upload)
  db.session.commit()

  return {
    'data': {
      'uploadID': upload.id,
      'partSize': part_size,
      'totalParts': part_count,
      'options': {},
    }
  }

@registry.handles(
  rule='/v2/imagefile/<string:image_id>/_multipart',
  method='PUT',
  authenticators=authenticator.with_scope(Scopes.user),
  request_body_schema=MultiImageFilePartSchema(),
  response_body_schema=ImageFilePostPartResponseSchema(),
)
def push_image_v2_multi_part(image_id):
  image = _get_image_id(image_id)
  body = rebar.validated_body

  upload = ImageUploadUrl.query.get(body.get('uploadID'))
  if upload.type != UploadTypes.multipart:
    raise errors.NotAcceptable(f"UploadID {upload.id} is not a multipart upload")
  if upload.state == UploadStates.completed or upload.state == UploadStates.failed:
    raise errors.NotAcceptable(f"UploadID {upload.id} already closed ({upload.state})")
  if body.get('partNumber') < 0 or body.get('partNumber') > upload.totalParts:
    raise errors.NotAcceptable(f"Invalid part number {body.get('partNumber')}")

  part = ImageUploadUrl.query.filter(
    ImageUploadUrl.partNumber==body.get('partNumber'),
    ImageUploadUrl.parent_ref==upload
  ).first()

  if not part:
    with tempfile.NamedTemporaryFile(dir=upload.path, delete=False) as tmpf:
      part = ImageUploadUrl(
        image_id=image.id,
        size=body.get('partSize'),
        partNumber=body.get('partNumber'),
        totalParts=upload.totalParts,
        sha256sum=body.get('sha256sum'),
        path=tmpf.name,
        state=UploadStates.initialized,
        type=UploadTypes.multipart_chunk,
        owner=g.authenticated_user,
        parent_ref=upload,
      )
    db.session.add(part)

  upload.state=UploadStates.uploading
  db.session.commit()

  upload_url = _get_service_url()+f"/v2/imagefile/_upload/{part.id}"
  return {
    'data': {
      'presignedURL': upload_url,
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
  if upload.expiresAt < datetime.now():
    raise errors.NotAcceptable(f"Upload already expired. Please to be faster.")
  
  upload.state=UploadStates.uploading
  db.session.commit()
  fd, read = _receive_upload(open(upload.path, "wb"), f"sha256.{upload.sha256sum}")

  if read != upload.size:
    current_app.logger.error(f"Upload size mismatch {read}!={upload.size}")
    raise errors.UnprocessableEntity(f"Image size {read} does not match announced size: {upload.size}")

  upload.state=UploadStates.uploaded
  db.session.commit()
  
  response = make_response('Danke!')
  response.headers.set('ETag', upload.sha256sum)
  return response

@registry.handles(
  rule='/v2/imagefile/<string:image_id>/_complete',
  method='PUT',
  request_body_schema=UploadImageCompleteRequest(),
  response_body_schema=ImageFileCompleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image_v2_complete(image_id):
  image = _get_image_id(image_id)
  upload = image.uploads_ref.filter(ImageUploadUrl.state == UploadStates.uploaded, ImageUploadUrl.type == UploadTypes.single).order_by(ImageUploadUrl.createdAt.desc()).first()
  if not upload:
    raise errors.NotFound(f"No valid upload for {image_id} found")
  if not upload.check_access(g.authenticated_user):
    raise errors.Forbidden(f"Not allowed to access image")

  try:
    _move_image(upload.path, image)
  except Exception as exc:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    raise exc

  upload.state = UploadStates.completed
  db.session.commit()
  return {
    'data': {
      'quota': {
        # XXX
        'quotaTotal': 0,
        'quotaUsage': 0,
      },
      'containerUrl': f"entities/{image.container_ref.entityName()}/collections/{image.container_ref.collectionName()}/containers/{image.container_ref.name}"
    }
  }

@registry.handles(
  rule='/v2/imagefile/<string:image_id>/_multipart_complete',
  method='PUT',
  request_body_schema=MultiUploadImageCompleteRequest(),
  response_body_schema=ImageFileCompleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image_v2_multi_complete(image_id):
  image = _get_image_id(image_id)
  body = rebar.validated_body
  upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == body.get('uploadID')).first()
  if not upload:
    current_app.logger.debug(f"Upload {body.get('uploadID')} not found")
    raise errors.NotFound(f"Upload ID {body.get('uploadID')} not found")
  if not upload.check_access(g.authenticated_user):
    current_app.logger.error(f"Access denied to upload")
    raise errors.Forbidden(f"Not allowed to access upload")
  if not upload.type == UploadTypes.multipart:
    raise errors.NotAcceptable(f"Not a multipart upload")

  try:
    _rebuild_chunks(upload)
  except Exception as exc:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    raise exc

  return {
    'data': {
      'quota': {
        # XXX
        'quotaTotal': 0,
        'quotaUsage': 0,
      },
      'containerUrl': f"entities/{image.container_ref.entityName()}/collections/{image.container_ref.collectionName()}/containers/{image.container_ref.name}"
    }
  }

@registry.handles(
  rule='/v2/imagefile/<string:image_id>/_multipart_abort',
  method='PUT',
  request_body_schema=MultiUploadImageAbortRequest(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image_v2_multi_abort(image_id):
  image = _get_image_id(image_id)
  body = rebar.validated_body

  upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == body.get('uploadID')).first()
  if not upload:
    raise errors.NotFound(f"Upload {body.get('uploadID')} not found")

  for part in upload.parts_ref:
    part.state = UploadStates.failed
  upload.state = UploadStates.failed
  image.uploaded = False
  image.location = None
  db.session.commit()

  return 'Sorry it did not work out'


@registry.handles(
  rule='/v1/imagefile/<string:image_id>',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user),
)
def push_image(image_id):
  image = _get_image_id(image_id)

  upload_tmp = os.path.join(current_app.config['IMAGE_PATH'], '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  tmpf, _ = _receive_upload(tempfile.NamedTemporaryFile('wb', delete=False, dir=upload_tmp), image.hash)
  _move_image(tmpf.name, image)

  return 'Danke!'

def _make_filename(image: Image) -> str:
  outfn = safe_join(current_app.config.get('IMAGE_PATH'), '_imgs', image.make_filename())
  os.makedirs(os.path.dirname(outfn), exist_ok=True)
  return outfn

def _move_image(tmpf: str, image: Image) -> Image:
  outfn = _make_filename(image)

  new_size = os.path.getsize(tmpf)
  entity = image.container_ref.collection_ref.entity_ref
  if entity.quota != 0 and entity.used_quota + new_size > entity.quota:
    raise errors.RequestEntityTooLarge(f'quota exceeded')

  current_app.logger.debug(f"moving image from {tmpf} to {outfn}")
  shutil.move(tmpf, outfn)
  image.location=os.path.abspath(outfn)
  image.size=os.path.getsize(image.location)
  image.uploaded=True
  entity.calculate_used()
  db.session.commit()

  try:
    current_app.logger.debug("checking signature(s)...")
    sigdata = image.check_signature()
    if image.signed:
      current_app.logger.debug("... signed")
    db.session.commit()
  except Exception as err:
    current_app.logger.warning(f"Image signature check failed: {err}")
   
  # XXX another race condition
  if image.media_type == Image.singularity_media_type:
    image.container_ref.tag_image('latest', image.id, arch=current_app.config.get('DEFAULT_ARCH', 'amd64'))
  return image


def _receive_upload(tmpf: IO, checksum: str=None) -> Tuple[IO, int]:
  m = hashlib.sha256()
  #current_app.logger.debug(f"starting upload to {tmpf.name}")

  read = 0
  while (True):
    chunk = request.stream.read(current_app.config.get("UPLOAD_CHUNK_SIZE", 16385))
    if len(chunk) == 0:
      break
    read = read + len(chunk)
    m.update(chunk)
    tmpf.write(chunk)
  
  #current_app.logger.debug(f"calculating checksum...")
  digest = m.hexdigest()
  if checksum and checksum != f"sha256.{digest}":
    current_app.logger.error(f"upload checksum mismatch {checksum}!={digest}")
    raise errors.UnprocessableEntity(f"Image hash {checksum} does not match: {digest}")
  tmpf.close()
  return tmpf, read


def _rebuild_chunks(upload: ImageUploadUrl):
  chunks=[]
  for chunk in upload.parts_ref.order_by(ImageUploadUrl.partNumber.asc()):
    if not chunk.state == UploadStates.uploaded:
      raise errors.NotAcceptable(f"Part {chunk.partNumber} not uploaded yet")
    if not chunk.size:
      current_app.logger.debug(f"skip empty chunk {chunk.partNumber}")
      chunk.state = UploadStates.completed
      continue

    chunks.append(chunk)
  if upload.totalParts is not None and len(chunks) != upload.totalParts:
    raise errors.NotAcceptable(f"Received only {len(chunks)}/{upload.totalParts}")

  current_app.logger.debug(f"rebuild from {len(chunks)} chunks")
  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  m = hashlib.sha256()
  tmpf = tempfile.NamedTemporaryFile('wb', dir=upload_tmp, delete=False)
  for chunk in chunks:
    try:
      with open(chunk.path, "rb") as chunk_fh:
        chunk_data = chunk_fh.read()
        m.update(chunk_data)
        tmpf.file.write(chunk_data)

      chunk.state=UploadStates.completed
    except FileNotFoundError:
      db.session.rollback()
      chunk.state=UploadStates.failed
      db.session.commit()
      raise errors.InternalError(f"file not found: {chunk.path}")
  digest = m.hexdigest()
  if upload.image_ref.hash != f"sha256.{digest}":
    current_app.logger.error(f"Invalid checksum {upload.image_ref.hash}/{digest}")
    raise errors.UnprocessableEntity(f"Announced hash {upload.image_ref.hash} does not match final hash {digest}")
  tmpf.close()
  _move_image(tmpf.name, upload.image_ref)
  upload.state = UploadStates.completed
  db.session.commit()