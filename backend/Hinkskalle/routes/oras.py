from Hinkskalle.routes import manifests
from Hinkskalle.models.User import Token
from flask import current_app, make_response, send_file, jsonify, g, request
from flask_rebar import errors

from typing import List, Tuple
from hashlib import sha256
from flask_rebar.validation import RequestSchema
from marshmallow import fields, Schema
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
import tempfile
import os
import os.path
from datetime import datetime, timedelta
import re
import base64

from werkzeug.exceptions import BadRequest

from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Image import Image
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models.User import User
from Hinkskalle.models import Manifest, Container, UploadTypes, UploadStates, ImageUploadUrl
from Hinkskalle import db, registry, authenticator, rebar, password_checkers

from Hinkskalle.util.auth.token import Scopes
from Hinkskalle.util.auth.exceptions import UserNotFound, UserDisabled, InvalidPassword
from .util import _get_container as __get_container, _get_service_url
from .imagefiles import _move_image, _receive_upload as __receive_upload, _rebuild_chunks
from .images import _delete_image

class OrasPushBlobQuerySchema(RequestSchema):
  digest = fields.String(required=True)

class OrasListTagQuerySchema(RequestSchema):
  n = fields.Integer(required=False)
  last = fields.String(required=False)

class OrasBlobMountQuerySchema(RequestSchema):
  private = fields.Bool(required=False)
  staged = fields.Bool(required=False)
  digest = fields.String(required=False)
  mount = fields.String(required=False)
  _from = fields.String(load_from='from', dump_to='from', attribute='from', required=False)

# see https://github.com/opencontainers/distribution-spec/blob/main/spec.md#error-codes
class OrasError(Exception):
  status_code = 500
  def __init__(self, detail: str=None, code: str=None, message: str=None):
    if code:
      self.code = code
    if message:
      self.message = message
    self.detail = detail
    super(OrasError, self).__init__(self.message)
  
class OrasNameUnknown(OrasError):
  status_code = 404
  code = 'NAME_UNKNOWN'
  message = 'repository name not known to registry'
  def __init__(self, detail: str=None):
    super().__init__(detail=detail)

class OrasNameInvalid(OrasError):
  status_code = 400
  code = 'NAME_INVALID'
  message = 'invalid repository name'

class OrasManifestUnknown(OrasError):
  status_code = 404
  code = 'MANIFEST_UNKNOWN'
  message = 'manifest unknown'

class OrasManifestInvalid(OrasError):
  status_code = 400
  code = 'MANIFEST_INVALID'
  message = 'manifest invalid'

class OrasBlobUnknwon(OrasError):
  status_code = 404
  code = 'BLOB_UNKNOWN'
  message = 'blob unknown to registry'

class OrasUnsupported(OrasError):
  status_code = 400
  code = 'UNSUPPORTED'
  message = 'the operation is unsupported'

class OrasDenied(OrasError):
  status_code = 403
  code = 'DENIED'
  message = 'requested access to the resource is denied'

class OrasUnauthorized(OrasError):
  status_code = 401
  code = 'UNAUTHORIZED'
  message = 'authentication required'

class OrasBlobUploadUnknown(OrasError):
  status_code = 404
  code = 'BLOB_UPLOAD_UNKNOWN'
  message = 'blob upload unknown to registry'

class OrasBlobUploadInvalid(OrasError):
  status_code = 400
  code = 'BLOB_UPLOAD_INVALID'
  message = 'blob upload invalid'

class OrasDigestInvalid(OrasError):
  status_code = 400
  code = 'DIGEST_INVALID'
  message = 'provided digest did not match uploaded content'

class OrasContentRangeInvalid(OrasError):
  status_code = 416
  code = 'RANGE_INVALID'
  message = 'Requested Range Not Satisfiable'

@current_app.errorhandler(OrasError)
def handle_oras_error(error: OrasError):
  body = {
    'errors': [
      { 'code': error.code, 'message': error.message, 'detail': error.detail }
    ]
  }
  resp = jsonify(body)
  resp.status_code = error.status_code
  if error.status_code == 401:
    resp.headers['WWW-Authenticate']=f'bearer realm="{_get_service_url()}/v2/"'
  return resp

@registry.handles(
  rule='/v2/',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.optional)
)
def authenticate_check():
  if g.authenticated_user:
    current_app.logger.debug(f"authenticated ok: {g.authenticated_user.username}")
    return jsonify({ 'msg': 'Hejsan!' })
  elif request.headers.get('Authorization'):
    current_app.logger.debug("checking basic auth...")
    auth_header = request.headers.get('Authorization')
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower()!='basic':
      raise OrasUnauthorized()
    decoded = base64.b64decode(parts[1]).decode('utf8')
    try:
      username, password = decoded.split(':')
    except ValueError:
      raise OrasUnauthorized()
    if not username or not password:
      current_app.logger.debug(f"Invalid basic auth data {decoded}")
      raise OrasUnauthorized()
    try:
      user = password_checkers.check_password(username, password)
    except (UserNotFound, UserDisabled, InvalidPassword) as err:
      current_app.logger.debug(f"password check fail {err}")
      raise OrasUnauthorized()
    token = user.create_token()
    token.refresh()
    token.source = 'auto'
    db.session.add(token)
    db.session.commit()
    return _auth_token(token)
  else:
    raise OrasUnauthorized()

@registry.handles(
  rule='/v2/',
  method='POST',
)
def authenticate():
  token = request.form.get('refresh_token')
  if not token:
    current_app.logger.debug(f"no token in form data")
    raise OrasUnauthorized('no token found')
  from Hinkskalle.util.auth.token import TokenAuthenticator
  try:
    db_token = TokenAuthenticator()._get_identity(token)
  except errors.Unauthorized as err:
    current_app.logger.debug(f"get identity: {err.error_message}")
    raise OrasUnauthorized(err.error_message)
  return _auth_token(db_token) 

def _auth_token(token: Token):
  expires_in: timedelta = token.expiresAt - datetime.now() if token.expiresAt else timedelta(days=366)
  return jsonify({
    "token_type": "Bearer",
    "expires_in": expires_in.seconds,
    "access_token": token.token,
    "scope": "all"
  })

# see https://github.com/opencontainers/distribution-spec/blob/main/spec.md#content-discovery
# XXX missing tag subsetting
@registry.handles(
  rule='/v2/<distname:name>/tags/list',
  method='GET',
  query_string_schema=OrasListTagQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def oras_list_tags(name: str):
  args = rebar.validated_args
  container = _get_container(name)
  if not container.check_access(g.authenticated_user):
    raise OrasDenied(f"Not your container")
  
  if args.get('n') is None or args.get('n') > 0:
    cur_tags: List[str] = [ t.name for t in Tag.query.filter(Tag.image_id.in_([ i.id for i in container.images_ref ])).order_by(Tag.name) ]
    if args.get('last') is not None:
      try:
        last_idx = cur_tags.index(args.get('last'))
      except ValueError:
        raise OrasManifestUnknown(f"Tag {args.get('last')} not found")
      cur_tags = cur_tags[last_idx+1:]
    if args.get('n'):
      cur_tags = cur_tags[:args.get('n')]
  else:
    cur_tags = []
  
  return {
    "name": f"{container.entityName()}/{container.collectionName()}/{container.name}",
    "tags": cur_tags
  }


# pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-manifests
# oras client fetches first with tag, then re-fetches manifest by sha hash
@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user),
)
def oras_manifest(name: str, reference: str):
  # should check accept header for 
  # application/vnd.oci.image.manifest.v1+json
  container = _get_container(name)
  if container.private or container.collection_ref.private:
    if not container.check_access(g.authenticated_user):
      raise OrasDenied(f"Container is private.")

  if reference.startswith('sha256:'):
    try:
      manifest = Manifest.query.filter(Manifest.hash==reference.replace('sha256:', '')).one()
    except NoResultFound:
      raise OrasManifestUnknown(f"Manifest {reference} not found")
  else:
    tag = container.get_tag(reference)
    if not tag:
      raise OrasManifestUnknown(f"Tag {reference} not found")
    
    if not tag.manifest_ref or tag.manifest_ref.stale:
      if tag.image_ref.media_type == Image.singularity_media_type:
        manifest = tag.image_ref.generate_manifest()
        tag.manifest_ref=manifest
      else:
        raise OrasManifestUnknown(f"Tag {reference} not found")
    else:
      manifest = tag.manifest_ref


  manifest_type = manifest.content_json.get('mediaType', 'application/vnd.oci.image.manifest.v1+json')

  if request.method != 'HEAD':
    manifest.downloadCount += 1
    manifest.latestDownload = datetime.now()
    db.session.commit()

  response = make_response(manifest.content)
  response.headers['Content-Type']=manifest_type
  response.headers['Docker-Content-Digest']=f'sha256:{manifest.hash}'
  return response
  

# blob pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-blobs
# we can only support sha256 (would need to pre-calculate more hashes)
@registry.handles(
  rule='/v2/<distname:name>/blobs/<string:digest>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user),
)
def oras_blob(name, digest):
  # check accept header for
  # application/vnd.sylabs.sif.layer.v1.sif
  if not digest.startswith('sha256:'):
    raise OrasUnsupported(f"only sha256 digest supported")
  
  container = _get_container(name)
  if container.private or container.collection_ref.private:
    if not container.check_access(g.authenticated_user):
      raise OrasDenied(f"Private container denied")
  try:
    image = container.images_ref.filter(Image.hash == f"sha256.{digest.replace('sha256:', '')}").one()
  except NoResultFound:
    current_app.logger.debug(f"hash {digest} for container {container.id} not found")
    raise OrasBlobUnknwon(f"Blob {digest} not found")
  
  if not image.uploaded or not image.location:
    raise OrasBlobUnknwon(f"Blob {digest} not uploaded or already deleted.")

  if request.method != 'HEAD':
    image.downloadCount += 1
    container.downloadCount += 1
    image.latestDownload = datetime.now()
    container.latestDownload = datetime.now()
    db.session.commit()
  
  ret = send_file(image.location)
  ret.headers['Docker-Content-Digest']=f"sha256:{image.hash}"
  return ret

@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='PUT',
  authenticators=authenticator.with_scope(Scopes.user)
)
def oras_push_manifest(name, reference):
  container = _get_container(name)
  if not container.check_access(g.authenticated_user):
    raise OrasDenied(f"Not your container")

  if container.readOnly:
    raise OrasDenied(f"Container is readonly")
  tag = container.get_tag(reference)

  try:
    manifest_data = request.json
  except BadRequest:
    current_app.logger.debug('Invalid JSON')
    raise OrasManifestInvalid()
  current_app.logger.debug(manifest_data)

  # XXX validate with schema

  if not tag:
    if len([ l for l in manifest_data.get('layers', []) if Image.valid_media_types.get(l.get('mediaType'))]) == 0:
      current_app.logger.debug(f"No tag {reference} on container {container.id} and no layers provided")
    tag = Tag(name=reference)
    db.session.add(tag)

  with db.session.no_autoflush:
    for layer in manifest_data.get('layers', []) + [ manifest_data.get('config', {})]:
      if not 'digest' in layer or not 'mediaType' in layer:
        continue
      try:
        image = Image.query.filter(Image.hash==layer.get('digest').replace('sha256:', 'sha256.'), Image.container_ref==container).one()
        image.media_type = layer.get('mediaType')
        if not image.hide:
          tag.image_ref=image
      except NoResultFound:
        current_app.logger.debug(f"Blob hash {layer.get('digest')} not found in container {container.id}")
        raise OrasBlobUnknwon(f"Blob hash {layer.get('digest')} not found in container {container.id}")

  with db.session.no_autoflush:
    manifest = tag.manifest_ref or Manifest()
    manifest.content = request.data.decode('utf8')
    existing = Manifest.query.filter(Manifest.hash == manifest.hash, Manifest.container_ref==container).first()
    if existing:
      if manifest in db.session:
        db.session.expunge(manifest)
      manifest = existing
    else:
      db.session.add(manifest)

  manifest.container_ref=container
  tag.container_ref=container
  tag.manifest_ref=manifest

  db.session.commit()
  
  manifest_url = _get_service_url()+f"/v2/{container.entityName()}/{container.collectionName()}/{container.name}/manifests/sha256:{manifest.hash}"
  response = make_response('', 201)
  response.headers['Location']=manifest_url
  response.headers['Docker-Content-Digest']=f'sha256:{manifest.hash}'
  return response



@registry.handles(
  rule='/v2/<distname:name>/blobs/uploads/',
  method='POST',
  query_string_schema=OrasBlobMountQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def oras_start_upload_session(name):
  args = rebar.validated_args
  headers = request.headers

  try:
    container = _get_container(name)
  except OrasNameUnknown:
    current_app.logger.debug(f"creating {name}...")
    entity_id, collection_id, container_id = _split_name(name)
    owner = g.authenticated_user
    if g.authenticated_user.is_admin:
      entity_user = User.query.filter(User.username==entity_id).first()
      if entity_user:
        owner = entity_user

    # XXX superhack-altert
    # singularity starts two uploads immediately (config + container)
    # this causes a race condition if container/... did not exist
    # one upload creates, the other one tries too and crashes
    try:
      try:
        entity = Entity.query.filter(func.lower(Entity.name)==entity_id.lower()).one()
        if g.authenticated_user.is_admin:
          owner = entity.owner
      except NoResultFound:
        if not g.authenticated_user.is_admin and entity_id.lower() != g.authenticated_user.username.lower():
          current_app.logger.debug(f"User {g.authenticated_user.username} tried to create {entity_id}")
          raise OrasDenied(f"Can only push to username entity")

        current_app.logger.debug(f"... creating entity {entity_id}")
        entity = Entity(name=entity_id, owner=owner)
        db.session.add(entity)
      try:
        collection = entity.collections_ref.filter(func.lower(Collection.name)==collection_id.lower()).one()
      except NoResultFound:
        if not entity.check_update_access(g.authenticated_user):
          current_app.logger.debug(f"User {g.authenticated_user.username} tried to create {entity_id}/{collection_id}")
          raise OrasDenied(f"Cannot create collections in {entity.name}")

        current_app.logger.debug(f"... creating collection {collection_id}")
        collection = Collection(name=collection_id, entity_ref=entity, owner=owner)
        if entity.defaultPrivate or args.get('private'):
          collection.private=True
        db.session.add(collection)
        db.session.commit()
      try:
        container = collection.containers_ref.filter(func.lower(Container.name)==container_id.lower()).one()
      except NoResultFound:
        if not collection.check_update_access(g.authenticated_user):
          current_app.logger.debug(f"User {g.authenticated_user.username} tried to create {entity_id}/{collection_id}/{container_id}")
          raise OrasDenied(f"Cannot create containers in {entity_id}/{collection_id}")

        current_app.logger.debug(f"... creating container {container_id}")
        container = Container(name=container_id, collection_ref=collection, owner=owner)
        if collection.private or args.get('private'):
          container.private=True
        db.session.add(container)
        db.session.commit()
    except IntegrityError:
      db.session.rollback()
      current_app.logger.debug(f"race condition alert")
      container = _get_container(name)

  if not container.check_update_access(g.authenticated_user):
    raise OrasDenied(f"Not your container")
  
  if container.readOnly:
    raise OrasDenied(f"Container is readonly")

  if args.get('private'):
    current_app.logger.debug('set private')
    container.private = True
  
  if args.get('from') and args.get('mount'):
    return _do_mount(container=container, _from=args.get('from'), mount=args.get('mount'))

  upload_tmp = os.path.join(current_app.config['IMAGE_PATH'], '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)

  image = Image(container_ref=container, owner=g.authenticated_user, media_type='unknown')
  db.session.add(image)

  with tempfile.NamedTemporaryFile(dir=upload_tmp, delete=False) as tmpf:
    upload = ImageUploadUrl(
      path=tmpf.name,
      state=UploadStates.initialized,
      owner=g.authenticated_user,
      type=UploadTypes.undetermined,
      image_ref=image
    )
  db.session.add(upload)
  db.session.commit()

  if args.get('staged', False) or (headers.get('content_type')=='application/octet-stream' and int(headers.get('content_length', 0)) > 0): 
    return _do_single_post_upload(upload, digest=args.get('digest'), staged=args.get('staged', False))

  upload_url = _get_service_url()+f"/v2/__uploads/{upload.id}"


  response = make_response('', 202)
  response.headers.remove('Content-Type')
  response.headers['Location']=upload_url
  return response

def _do_single_post_upload(upload: ImageUploadUrl, digest: str, staged: bool = False):
  current_app.logger.debug(f"single POST update")
  if staged and not g.authenticated_user.is_admin:
    current_app.logger.debug("deny staged upload for user")
    raise OrasDenied('cannot use staged upload')
  upload.type = UploadTypes.single
  if not digest:
    raise OrasDigestInvalid(f"need digest for single push upload")
  digest = digest.replace('sha256:', 'sha256.')
  image = _receive_upload(upload, digest, staged=staged)
  blob_url = _get_service_url()+f"/v2/{image.container_ref.entityName()}/{image.container_ref.collectionName()}/{image.container_ref.name}/blobs/{image.hash.replace('sha256.', 'sha256:')}"
  response = make_response('', 201)
  response.headers['Location']=blob_url
  response.headers['Docker-Content-Digest']=f"{image.hash.replace('sha256.', 'sha256:')}"
  return response


def _do_mount(container: Container, _from: str, mount: str):
  current_app.logger.debug('cross repo mount')
  from_container = _get_container(_from)
  try:
    from_image = Image.query.filter(Image.container_id==from_container.id, Image.hash==mount.replace('sha256:', 'sha256.')).one()
  except NoResultFound:
    raise OrasBlobUnknwon(f"mounting blob {mount} from {_from}: not found")
  image = Image(
    container_ref=container, 
    owner=g.authenticated_user, 
    hash=from_image.hash,
    size=from_image.size,
    uploaded=from_image.uploaded,
    arch=from_image.arch,
    signed=from_image.signed,
    signatureVerified=from_image.signatureVerified,
    encrypted=from_image.encrypted,
    sigdata=from_image.sigdata,
    media_type=from_image.media_type,
    location=from_image.location,
  )
  db.session.add(image)
  db.session.commit()
  blob_url = _get_service_url()+f"/v2/{image.container_ref.entityName()}/{image.container_ref.collectionName()}/{image.container_ref.name}/blobs/{image.hash.replace('sha256.', 'sha256:')}"
  response = make_response('', 201)
  response.headers['Location']=blob_url
  response.headers['Docker-Content-Digest']=f"{image.hash.replace('sha256.', 'sha256:')}"
  return response

@registry.handles(
  rule='/v2/__uploads/<string:upload_id>',
  method='PATCH',
)
def oras_push_chunk_init(upload_id):
  try:
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == upload_id).one()
  except NoResultFound:
    raise OrasBlobUploadUnknown()
  
  if upload.type == UploadTypes.undetermined:
    if upload.state != UploadStates.initialized:
      current_app.logger.debug(f"Upload {upload.id} has {upload.type}/{upload.state}")
      raise OrasBlobUploadInvalid(f"Upload {upload.id} has invalid state")
    upload.type = UploadTypes.multipart
  else:
    current_app.logger.debug(f"Upload {upload.id} has {upload.type}/{upload.state}")
    raise OrasBlobUploadInvalid(f"Upload {upload.id} has invalid state")
  
  if upload.expiresAt < datetime.now():
    current_app.logger.debug(f"Upload expired at {upload.expiresAt}")
    raise OrasBlobUploadInvalid(f"Upload already expired. Please to be faster.")
  upload.state = UploadStates.uploading

  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)
  upload.path = tempfile.mkdtemp(dir=upload_tmp)

  with tempfile.NamedTemporaryFile(dir=upload.path, delete=False) as tmpf:
    chunk = ImageUploadUrl(
      image_id = upload.image_id,
      partNumber = 1,
      path=tmpf.name,
      state=UploadStates.initialized,
      type=UploadTypes.multipart_chunk,
      parent_ref=upload
    )
  db.session.add(chunk)
  db.session.commit()
  _handle_chunk(chunk)
  next_chunk = _next_chunk(upload, chunk)
  return next_chunk


@registry.handles(
  rule='/v2/__uploads/<string:upload_id>/<string:chunk_id>',
  method='PATCH',
)
def oras_push_chunk(upload_id, chunk_id):
  upload, chunk = _get_chunk(upload_id, chunk_id)
  _handle_chunk(chunk)
  return _next_chunk(upload, chunk)

@registry.handles(
  rule='/v2/__uploads/<string:upload_id>/<string:chunk_id>',
  query_string_schema=OrasPushBlobQuerySchema(),
  method='PUT'
)
def oras_push_chunk_finish(upload_id, chunk_id):
  args = rebar.validated_args
  upload, chunk = _get_chunk(upload_id, chunk_id)
  if int(request.headers.get('content_length', 0)) > 0:
    _handle_chunk(chunk)
  else:
    chunk.state = UploadStates.uploaded
  
  digest = args.get('digest').replace('sha256:', 'sha256.')
  existing = Image.query.filter(Image.hash == digest, Image.container_id==upload.image_ref.container_id).first()
  if existing:
    current_app.logger.debug(f"Re-using existing image {existing.id} with same hash {digest}")
    to_delete = upload.image_ref
    upload.image_ref=existing
    for sub in ImageUploadUrl.query.filter(ImageUploadUrl.image_id==to_delete.id):
      sub.image_ref=existing
    db.session.commit()
    # commit before deleting, otherwise sqlalchemy's soft-cascade will
    # kill the upload too
    db.session.delete(to_delete)
  else:
    upload.image_ref.hash = digest

  try:
    _rebuild_chunks(upload)
  except errors.NotAcceptable as err:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    current_app.logger.debug(f"rebuild chunks {err}")
    raise OrasBlobUploadInvalid(err.error_message)
  except errors.UnprocessableEntity as err:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    current_app.logger.debug(f"rebuild chunks {err}")
    raise OrasDigestInvalid(err.error_message)
  except Exception as err:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    raise err

  
  blob_url = _get_service_url()+f"/v2/{upload.image_ref.entityName()}/{upload.image_ref.collectionName()}/{upload.image_ref.containerName()}/blobs/{upload.image_ref.hash.replace('sha256.', 'sha256:')}"
  response = make_response('', 201)
  response.headers['Location']=blob_url
  response.headers['Docker-Content-Digest']=f"{upload.image_ref.hash.replace('sha256.', 'sha256:')}"
  return response


def _get_chunk(upload_id: str, chunk_id: str) -> Tuple[ImageUploadUrl, ImageUploadUrl]:
  try:
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == upload_id).one()
  except NoResultFound:
    raise OrasBlobUploadUnknown()
  
  if upload.type != UploadTypes.multipart:
    current_app.logger.debug(f"Invalid upload type {upload.type}")
    raise OrasBlobUploadInvalid(f"Not a multipart upload")
  if upload.state != UploadStates.uploading:
    current_app.logger.debug(f"Invalid upload state {upload.state}")
    raise OrasBlobUploadInvalid(f"Invalid upload state")
  
  try:
    chunk = ImageUploadUrl.query.filter(ImageUploadUrl.id==chunk_id, ImageUploadUrl.parent_id == upload.id).one()
  except NoResultFound:
    raise OrasBlobUploadUnknown()
  
  if chunk.expiresAt < datetime.now():
    current_app.logger.debug(f"Chunk expired at {chunk.expiresAt}")
    raise OrasBlobUploadInvalid(f"Upload already expired. Please to be faster.")
  if chunk.state != UploadStates.initialized:
    current_app.logger.debug(f"Invalid chunk state {chunk.state}")
    raise OrasBlobUploadInvalid(f"Invalid chunk state")
  return upload, chunk


def _handle_chunk(chunk: ImageUploadUrl):
  if request.headers.get('content_type') != 'application/octet-stream':
    current_app.logger.debug(f"Invalid content type {request.headers.get('content_type')}")
    # XXX docker push does not send content-type
    #raise OrasUnsupported(f"Invalid content type {request.headers.get('content_type')}")
  
  begin, end = None, None
  if not request.headers.get('Content-Range'):
    current_app.logger.debug(f"No content-range header found")
    # /v2/__uploads/d5d0d44c-b827-4baf-8423-9afeae6b4040
    # says there must be a content-range header, but the 
    # conformance tests don't send one?!
    #raise OrasBlobUploadInvalid(f"No content-range header found")
  else:
    range = request.headers.get('content_range', '')
    if not re.match(r'^[0-9]+-[0-9]+$', range):
      current_app.logger.debug(f"Invalid content range {range}")
      raise OrasBlobUploadInvalid(f"Invalid content range")
    begin, end = range.split('-')
    begin, end = int(begin), int(end)
    if chunk.partNumber == 1 and begin != 0:
      raise OrasContentRangeInvalid(f"first chunk must start with 0")

  if not request.headers.get('content_length'):
    current_app.logger.debug(f"No content-length header found")
    # XXX docker push does not send content-length?
    #raise OrasBlobUploadInvalid(f"No content-length header found")
  

  chunk.state = UploadStates.uploading

  _, read = __receive_upload(open(chunk.path, "wb"))
  if request.headers.get('content_length') and read != int(request.headers.get('content_length', -1)):
    current_app.logger.debug(f"Content length header mismatch {read}/{request.headers['content_length']}")
    raise OrasBlobUploadInvalid(f"Content length header mismatch")

  if begin is not None and end is not None and read != end - begin + 1:
    current_app.logger.debug(f"read {read} bytes, should be {end-begin+1} from content range {begin}-{end}")
    raise OrasBlobUploadInvalid(f"content range header does not compute")
  
  chunk.size = read
  chunk.state = UploadStates.uploaded
  #current_app.logger.debug(f"uploaded {chunk.size}b part {chunk.partNumber} for upload {chunk.parent_ref.id}")
  
def _next_chunk(upload, chunk):
  with tempfile.NamedTemporaryFile(dir=upload.path, delete=False) as tmpf:
    next_part = ImageUploadUrl(
      image_id = upload.image_id,
      partNumber = chunk.partNumber +1,
      path = tmpf.name,
      state = UploadStates.initialized,
      type = UploadTypes.multipart_chunk,
      parent_ref = upload,
    )
  db.session.add(next_part)

  db.session.commit()

  next_chunk = _get_service_url()+f"/v2/__uploads/{upload.id}/{next_part.id}"
  response = make_response(b'', 202)
  response.headers.remove('Content-Type')
  response.headers['Location'] = next_chunk
  response.headers['Range']=f'0-{chunk.size}'
  return response

  

@registry.handles(
  rule='/v2/__uploads/<string:upload_id>',
  method='PUT',
  query_string_schema=OrasPushBlobQuerySchema(),
)
def oras_push_registered(upload_id):
  args = rebar.validated_args
  headers = request.headers
  if headers['content_type'] != 'application/octet-stream':
    raise OrasUnsupported(f"Invalid content type {headers['content_type']}")

  if not args['digest'].startswith('sha256:'):
    raise OrasUnsupported('Only sha256 digest supported')
  digest = args['digest'].replace('sha256:', 'sha256.')

  try:
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == upload_id).one()
  except NoResultFound:
    raise OrasBlobUploadUnknown()

  # fresh upload, can still become single upload
  # if we had received a PATCH before this would have been changed to multipart
  if upload.type != UploadTypes.undetermined:
    current_app.logger.debug(f"Invalid upload type {upload.type} for {upload.id}")
    raise OrasBlobUploadInvalid(f"Invalid upload type {upload.type}")

  if upload.state != UploadStates.initialized:
    current_app.logger.debug(f"Upload {upload.id} has invalid state")
    raise OrasBlobUploadInvalid(f"Upload {upload.id} has invalid state")
  if upload.expiresAt < datetime.now():
    current_app.logger.debug(f"Upload {upload.id} expired")
    raise OrasBlobUploadInvalid(f"Upload already expired. Please to be faster.")
  upload.type = UploadTypes.single

  try:
    image = _receive_upload(upload, digest)
  except Exception as exc:
    db.session.rollback()
    upload.state = UploadStates.failed
    db.session.commit()
    raise exc
  
  blob_url = _get_service_url()+f"/v2/{image.container_ref.entityName()}/{image.container_ref.collectionName()}/{image.container_ref.name}/blobs/{image.hash.replace('sha256.', 'sha256:')}"
  response = make_response('', 201)
  response.headers['Location']=blob_url
  response.headers['Docker-Content-Digest']=f"{image.hash.replace('sha256.', 'sha256:')}"
  return response

# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#deleting-tags
# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#deleting-manifests
@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='DELETE',
  authenticators=authenticator.with_scope(Scopes.user)
)
def delete_reference(name, reference):
  container = _get_container(name)
  if not container.check_access(g.authenticated_user):
    raise OrasDenied(f"Not your container")
  if reference.startswith('sha256:'):
    try:
      manifest = Manifest.query.filter(Manifest.hash==reference.replace('sha256:', '')).one()
      # XXX it's not entirely clear to me if manifest delete should
      # also delete all tags associated with it.
      # but since we auto-vivify manifests on tag pull this might 
      # be the expected behavior (manifest is really gone, doesn't comes alive again)
      Tag.query.filter(Tag.manifest_id==manifest.id).delete()
      db.session.delete(manifest)
      db.session.commit()
    except NoResultFound:
      raise OrasManifestUnknown(f"Manifest {reference} not found")
  else:
    tag = container.get_tag(reference)
    if not tag:
      raise OrasManifestUnknown(f"Tag {reference} not found")
    db.session.delete(tag)
    db.session.commit()
    
  return make_response({}, 202)


# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#deleting-blobs
@registry.handles(
  rule='/v2/<distname:name>/blobs/<string:digest>',
  method='DELETE',
  authenticators=authenticator.with_scope(Scopes.user)
)
def delete_blob(name, digest):
  container = _get_container(name)
  if not container.check_access(g.authenticated_user):
    raise OrasDenied(f"Not your container")
  if not digest.startswith('sha256:'):
    raise OrasUnsupported(f"only sha256 digest supported")
  
  container = _get_container(name)
  try:
    image = container.images_ref.filter(Image.hash == f"sha256.{digest.replace('sha256:', '')}").one()
  except NoResultFound:
    current_app.logger.debug(f"hash {digest} for container {container.id} not found")
    raise OrasBlobUnknwon(f"Blob {digest} not found")
  
  _delete_image(image)
  return make_response({}, 202)

def _split_name(name: str) -> Tuple[str, str, str]:
  parts = name.split('/')
  if len(parts) == 1:
    entity='default'
    collection='default'
    container=parts[0]
  elif len(parts) == 2:
    entity='default'
    collection=parts[0]
    container=parts[1]
  elif len(parts) == 3:
    entity = parts[0]
    collection = parts[1]
    container = parts[2]
  else:
    raise OrasNameInvalid(f"name {name} is illegal")
  return entity, collection, container


def _get_container(name: str) -> Container:
  entity, collection, container = _split_name(name)
  
  try:
    container = __get_container(entity, collection, container)
  except errors.NotFound:
    raise OrasNameUnknown(f"name {name} not found")
  return container

def _receive_upload(upload: ImageUploadUrl, digest: str, staged: bool=False) -> Image:
  # we don't know the hash when upload is initialized
  # so we have to check if there is already an image in the container
  # with the same hash. If yes, re-use that one and get rid of the
  # temporary image created earlier.
  existing = Image.query.filter(Image.hash==digest, Image.container_id==upload.image_ref.container_id).first()
  if existing:
    current_app.logger.debug(f"Re-using existing image {existing.id} with same hash")
    to_delete = upload.image_ref
    upload.image_ref=existing
    db.session.commit()
    # commit before deleting, otherwise sqlalchemy's soft-cascade will
    # kill the upload too
    db.session.delete(to_delete)
  
  upload.state = UploadStates.uploading
  db.session.commit()

  if staged:
    staged_path = os.path.join(current_app.config['STAGING_PATH'], digest)
    if not os.path.exists(staged_path):
      current_app.logger.debug(f"Staged path {staged_path} not found")
      upload.state = UploadStates.failed
      db.session.commit()
      raise OrasBlobUploadInvalid(f"Staged path {staged_path} not found")
    read = os.path.getsize(staged_path)
    upload.path = staged_path
  else:
    try:
      _, read = __receive_upload(open(upload.path, 'wb'), digest)
    except errors.UnprocessableEntity:
      upload.state = UploadStates.failed
      db.session.commit()
      raise OrasDigestInvalid()
  # OCI spec says content-length is MUST, but ORAS push PUTs without??
  if not staged and request.headers.get('content_length') is not None and read != int(request.headers['content_length']):
    current_app.logger.debug(f"content length {read} did not match header {request.headers['content_length']}")
    upload.state = UploadStates.failed
    db.session.commit()
    raise OrasBlobUploadInvalid(f"content length {read} did not match header {request.headers['content_length']}")
  
  image = upload.image_ref
  image.hash = digest 
  _move_image(upload.path, image)
  upload.state = UploadStates.completed
  # hide until we receive the manifest
  image.hide=True 
  db.session.commit()
  return image
