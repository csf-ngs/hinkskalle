from flask import current_app, make_response, send_file, jsonify, g, request
from flask_rebar import errors

from typing import Tuple
from hashlib import sha256
from flask_rebar.validation import RequestSchema
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
import tempfile
import os
import os.path
from datetime import datetime

from werkzeug.utils import redirect

from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Image import Image
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models import Manifest, Container, UploadTypes, UploadStates, ImageUploadUrl
from Hinkskalle import db, registry, authenticator, rebar

from Hinkskalle.util.auth.token import Scopes
from .util import _get_container as __get_container, _get_service_url
from .imagefiles import _move_image, _receive_upload

class OrasPushBlobQuerySchema(RequestSchema):
  digest = fields.String(required=True)
class OrasPushBlobHeaderSchema(Schema):
  content_length = fields.Integer(required=True)
  content_type = fields.String(required=True)


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

@current_app.errorhandler(OrasError)
def handle_oras_error(error: OrasError):
  body = {
    'errors': [
      { 'code': error.code, 'message': error.message, 'detail': error.detail }
    ]
  }
  resp = jsonify(body)
  resp.status_code = error.status_code
  return resp


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

# pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-manifests
# oras client fetches first with tag, then re-fetches manifest by sha hash
@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.optional),
)
def oras_manifest(name: str, reference: str):
  # should check accept header for 
  # application/vnd.oci.image.manifest.v1+json
  container = _get_container(name)
  if reference.startswith('sha256:'):
    try:
      manifest = Manifest.query.filter(Manifest.hash==reference.replace('sha256:', '')).one()
    except NoResultFound:
      raise OrasManifestUnknown(f"Manifest {reference} not found")
  else:
    image_tags = container.imageTags()
    tag = container.get_tag(reference)
    if not tag:
      raise OrasManifestUnknown(f"Tag {reference} not found")
    
    manifest = tag.generate_manifest()
  db.session.add(manifest)
  db.session.commit()

  response = make_response(manifest.content)
  response.headers['Content-Type']='application/vnd.oci.image.manifest.v1+json'
  response.headers['Docker-Content-Digest']=f'sha256:{manifest.hash}'
  return response
  

# blob pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-blobs
# we can only support sha256 (would need to pre-calculate more hashes)
@registry.handles(
  rule='/v2/<distname:name>/blobs/<string:digest>',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.optional),
)
def oras_blob(name, digest):
  # check accept header for
  # application/vnd.sylabs.sif.layer.v1.sif
  if not digest.startswith('sha256:'):
    raise OrasUnsupported(f"only sha256 digest supported")
  
  container = _get_container(name)
  try:
    image = container.images_ref.filter(Image.hash == f"sha256.{digest.replace('sha256:', '')}").one()
  except NoResultFound:
    current_app.logger.debug(f"hash {digest} for container {container.id} not found")
    raise OrasBlobUnknwon(f"Blob {digest} not found")
  
  return send_file(image.location) 

@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='PUT',
  authenticators=authenticator.with_scope(Scopes.user)
)
def oras_push_manifest(name, reference):
  container = _get_container(name)
  tag = container.get_tag(reference)
  manifest_data = request.json
  if not tag:
    if len(manifest_data.get('layers', [])) == 0:
      raise OrasManifestUnknown(f"No tag {reference} on container {container.id} and no layers provided")
    tag = Tag(name=reference)
    db.session.add(tag)
  # XXX validate with schema

  with db.session.no_autoflush:
    for layer in manifest_data.get('layers', []):
      try:
        image = Image.query.filter(Image.hash==layer.get('digest').replace('sha256:', 'sha256.'), Image.container_ref==container).one()
        tag.image_ref=image
      except NoResultFound:
        raise OrasBlobUnknwon(f"Blob hash {layer.get('digest')} not found in container {container.id}")

  manifest = Manifest(content=request.json, tag_ref=tag)
  db.session.add(manifest)
  db.session.commit()
  
  manifest_url = _get_service_url()+f"/v2/{container.entityName()}/{container.collectionName()}/{container.name}/manifests/sha256:{manifest.hash}"
  return redirect(manifest_url, 201)



@registry.handles(
  rule='/v2/<distname:name>/blobs/upload/',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user)
)
def oras_start_upload_session(name):
  try:
    container = _get_container(name)
  except OrasNameUnknown:
    entity_id, collection_id, container_id = _split_name(name)
    try:
      entity = Entity.query.filter(func.lower(Entity.name)==entity_id.lower()).one()
    except NoResultFound:
      entity = Entity(name=entity_id, owner=g.authenticated_user)
      db.session.add(entity)
    try:
      collection = entity.collections_ref.filter(func.lower(Collection.name)==collection_id.lower()).one()
    except NoResultFound:
      collection = Collection(name=collection_id, entity_id=entity.id, owner=g.authenticated_user)
      db.session.add(collection)
    try:
      container = collection.containers_ref.filter(func.lower(Container.name)==container_id.lower()).one()
    except NoResultFound:
      container = Container(name=container_id, collection_id=collection.id, owner=g.authenticated_user)
      db.session.add(container)
  

  upload_tmp = os.path.join(current_app.config.get('IMAGE_PATH'), '_tmp')
  os.makedirs(upload_tmp, exist_ok=True)
  _, tmpf = tempfile.mkstemp(dir=upload_tmp)

  image = Image(container_ref=container)
  db.session.add(image)

  upload = ImageUploadUrl(
    path=tmpf,
    state=UploadStates.initialized,
    owner=g.authenticated_user,
    type=UploadTypes.single,
    image_ref=image
  )
  db.session.add(upload)
  db.session.commit()

  upload_url = _get_service_url()+f"/v2/__uploads/{upload.id}"

  return redirect(upload_url, 202)

@registry.handles(
  rule='/v2/__uploads/<string:upload_id>',
  method='PUT',
  query_string_schema=OrasPushBlobQuerySchema(),
  headers_schema=OrasPushBlobHeaderSchema(),
)
def oras_push_registered_single(upload_id):
  args = rebar.validated_args
  headers = rebar.validated_headers
  if headers['content_type'] != 'application/octet-stream':
    raise OrasUnsupported(f"Invalid content type {headers['content_type']}")

  if not args['digest'].startswith('sha256:'):
    raise OrasUnsupported('Only sha256 digest supported')
  digest = args['digest'].replace('sha256:', 'sha256.')

  try:
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.id == upload_id).one()
  except NoResultFound:
    raise OrasBlobUploadUnknown()

  if upload.state != UploadStates.initialized:
    raise OrasBlobUploadInvalid(f"Upload {upload.id} has invalid state")
  if upload.expiresAt < datetime.now():
    raise OrasBlobUploadInvalid(f"Upload already expired. Please to be faster.")
  
  upload.state = UploadStates.uploading
  db.session.commit()

  try:
    _, read = _receive_upload(open(upload.path, 'wb'), digest)
  except errors.UnprocessableEntity:
    raise OrasDigestInvalid()
  if read != headers['content_length']:
    raise OrasBlobUploadInvalid(f"content length did not match header")
  
  image = upload.image_ref
  image.hash = digest 
  _move_image(upload.path, image)
  upload.state = UploadStates.completed
  db.session.commit()
  
  blob_url = _get_service_url()+f"/v2/{image.container_ref.entityName()}/{image.container_ref.collectionName()}/{image.container_ref.name}/blobs/{image.hash.replace('sha256.', 'sha256:')}"
  return redirect(blob_url, 201)