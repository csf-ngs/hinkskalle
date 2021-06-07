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
from datetime import datetime

from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest

from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Image import Image
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models import Manifest, Container, UploadTypes, UploadStates, ImageUploadUrl
from Hinkskalle import db, registry, authenticator, rebar

from Hinkskalle.util.auth.token import Scopes
from .util import _get_container as __get_container, _get_service_url
from .imagefiles import _move_image, _receive_upload
from .images import _delete_image

class OrasPushBlobQuerySchema(RequestSchema):
  digest = fields.String(required=True)

class OrasListTagQuerySchema(RequestSchema):
  n = fields.Integer(required=False)
  last = fields.String(required=False)

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

# see https://github.com/opencontainers/distribution-spec/blob/main/spec.md#content-discovery
# XXX missing tag subsetting
@registry.handles(
  rule='/v2/<distname:name>/tags/list',
  method='GET',
  query_string_schema=OrasListTagQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.optional)
)
def oras_list_tags(name: str):
  args = rebar.validated_args
  container = _get_container(name)
  if container.private or container.collection_ref.private:
    raise OrasDenied(f"Container is private.")
  
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
  authenticators=authenticator.with_scope(Scopes.optional),
)
def oras_manifest(name: str, reference: str):
  # should check accept header for 
  # application/vnd.oci.image.manifest.v1+json
  container = _get_container(name)
  if container.private or container.collection_ref.private:
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
    
    # XXX check if manifest is up-to-date with image
    manifest = tag.manifest_ref or tag.generate_manifest()
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
  authenticators=authenticator.with_scope(Scopes.optional)
)
def oras_push_manifest(name, reference):
  container = _get_container(name)
  tag = container.get_tag(reference)

  try:
    manifest_data = request.json
  except BadRequest:
    raise OrasManifestInvalid()

  current_app.logger.debug(manifest_data)
  # XXX validate with schema

  if not tag:
    if len([ l for l in manifest_data.get('layers', []) if Image.valid_media_types.get(l.get('mediaType'))]) == 0:
      current_app.logger.debug(f"No tag {reference} on container {container.id} and no layers provided")
      raise OrasManifestUnknown(f"No tag {reference} on container {container.id} and no layers provided")
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
        raise OrasBlobUnknwon(f"Blob hash {layer.get('digest')} not found in container {container.id}")

  with db.session.no_autoflush:
    manifest = tag.manifest_ref or Manifest()
    manifest.content = request.data.decode('utf8')
    existing = Manifest.query.filter(Manifest.hash == manifest.hash).first()
    if existing:
      if manifest.id:
        db.session.delete(manifest)
      manifest = existing
    else:
      db.session.add(manifest)

  tag.manifest_ref=manifest

  db.session.commit()
  
  manifest_url = _get_service_url()+f"/v2/{container.entityName()}/{container.collectionName()}/{container.name}/manifests/sha256:{manifest.hash}"
  response = redirect(manifest_url, 201)
  response.headers['Docker-Content-Digest']=f'sha256:{manifest.hash}'
  return response



@registry.handles(
  rule='/v2/<distname:name>/blobs/uploads/',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.optional),
)
def oras_start_upload_session(name):
  headers = request.headers

  try:
    container = _get_container(name)
  except OrasNameUnknown:
    current_app.logger.debug(f"creating {name}...")
    entity_id, collection_id, container_id = _split_name(name)
    # XXX superhack-altert
    # singularity starts two uploads immediately (config + container)
    # this causes a race condition if container/... did not exist
    # one upload creates, the other one tries too and crashes
    try:
      entity = Entity.query.filter(func.lower(Entity.name)==entity_id.lower()).one()
    except NoResultFound:
      current_app.logger.debug(f"... creating entity {entity_id}")
      entity = Entity(name=entity_id, owner=g.authenticated_user)
      db.session.add(entity)
    try:
      collection = entity.collections_ref.filter(func.lower(Collection.name)==collection_id.lower()).one()
    except NoResultFound:
      current_app.logger.debug(f"... creating collection {collection_id}")
      collection = Collection(name=collection_id, entity_ref=entity, owner=g.authenticated_user)
      db.session.add(collection)
    try:
      container = collection.containers_ref.filter(func.lower(Container.name)==container_id.lower()).one()
    except NoResultFound:
      current_app.logger.debug(f"... creating container {container_id}")
      try:
        container = Container(name=container_id, collection_ref=collection, owner=g.authenticated_user)
        db.session.add(container)
        db.session.commit()
      except IntegrityError:
        db.session.rollback()
        current_app.logger.debug(f"race condition alert")
        container = _get_container(name)



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

  if headers.get('content_type')=='application/octet-stream' and headers.get('content_length', 0) > 0:
    current_app.logger.debug('single post push')
    raise OrasUnsupported(f"No single upload support yet")

  return redirect(upload_url, 202)

@registry.handles(
  rule='/v2/__uploads/<string:upload_id>',
  method='PUT',
  query_string_schema=OrasPushBlobQuerySchema(),
)
def oras_push_registered_single(upload_id):
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

  if upload.state != UploadStates.initialized:
    raise OrasBlobUploadInvalid(f"Upload {upload.id} has invalid state")
  if upload.expiresAt < datetime.now():
    raise OrasBlobUploadInvalid(f"Upload already expired. Please to be faster.")
  
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

  try:
    _, read = _receive_upload(open(upload.path, 'wb'), digest)
  except errors.UnprocessableEntity:
    upload.state = UploadStates.failed
    db.session.commit()
    raise OrasDigestInvalid()
  # OCI spec says content-length is MUST, but ORAS push PUTs without??
  if headers.get('content_length') is not None and read != int(headers['content_length']):
    current_app.logger.debug(f"content length {read} did not match header {headers['content_length']}")
    upload.state = UploadStates.failed
    db.session.commit()
    raise OrasBlobUploadInvalid(f"content length {read} did not match header {headers['content_length']}")
  
  image = upload.image_ref
  image.hash = digest 
  _move_image(upload.path, image)
  upload.state = UploadStates.completed
  # hide until we receive the manifest
  image.hide=True 
  db.session.commit()
  
  blob_url = _get_service_url()+f"/v2/{image.container_ref.entityName()}/{image.container_ref.collectionName()}/{image.container_ref.name}/blobs/{image.hash.replace('sha256.', 'sha256:')}"
  response = redirect(blob_url, 201)
  response.headers['Docker-Content-Digest']=f"{image.hash.replace('sha256.', 'sha256:')}"
  return response

# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#deleting-tags
# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#deleting-manifests
@registry.handles(
  rule='/v2/<distname:name>/manifests/<string:reference>',
  method='DELETE',
  authenticators=[authenticator.with_scope(Scopes.optional)]
)
def delete_reference(name, reference):
  container = _get_container(name)
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
  authenticators=[authenticator.with_scope(Scopes.optional)]
)
def delete_blob(name, digest):
  container = _get_container(name)
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