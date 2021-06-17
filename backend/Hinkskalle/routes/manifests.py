from flask.helpers import url_for
from flask_rebar.validation import RequestSchema
from Hinkskalle.util import auth
from Hinkskalle import registry, authenticator, rebar

from Hinkskalle.util.auth.token import Scopes

from flask import g, send_file, current_app, redirect
from flask_rebar import ResponseSchema, errors
from marshmallow import fields
from sqlalchemy.orm.exc import NoResultFound
import jwt
from datetime import datetime
from calendar import timegm

from Hinkskalle.models.Manifest import Manifest, ManifestSchema, ManifestTypes
from Hinkskalle.models.Image import Image
from Hinkskalle.models.User import User

from .util import _get_container

class ManifestListResponseSchema(ResponseSchema):
  data = fields.Nested(ManifestSchema, many=True)

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>/manifests',
  method='GET',
  response_body_schema=ManifestListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def list_manifests(entity_id, collection_id, container_id):
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  
  return { 'data': list(container.manifests_ref) }

class DownloadManifestQuerySchema(RequestSchema):
  temp_token=fields.String(required=False)


@registry.handles(
  rule='/v1/manifests/<string:manifest_id>/download',
  method='GET',
  query_string_schema=DownloadManifestQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.optional)
)
def download_manifest(manifest_id):
  args = rebar.validated_args
  if g.authenticated_user:
    user = g.authenticated_user
  elif args.get('temp_token'):
    try:
      decoded = jwt.decode(args.get('temp_token'), current_app.config['SECRET_KEY'], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
      raise errors.Unauthorized('token invalid')
    if decoded.get('type') != 'manifest':
      raise errors.NotAcceptable('invalid token, type should be manifest')
    if manifest_id != str(decoded.get('id')):
      raise errors.NotAcceptable('invalid token, id mismatch')
    try:
      user = User.query.filter(User.username==decoded.get('username')).one()
    except NoResultFound:
      raise errors.NotAcceptable('Invalid username')
  else:
    raise errors.Unauthorized()
  

  manifest: Manifest = Manifest.query.get(manifest_id)
  if not manifest:
    raise errors.NotFound('manifest not found')
  if not manifest.container_ref.check_access(user):
    raise errors.Forbidden('access denied')
  
  if manifest.type != ManifestTypes.singularity.name and manifest.type != ManifestTypes.oras.name:
    raise errors.NotAcceptable('can only download singularity and oras')
  
  fn = manifest.filename
  if fn == '(none)' or fn == '(multiple)':
    raise errors.NotAcceptable('unable to determine filename')
  
  if len(manifest.content_json.get('layers', [])) != 1:
    raise errors.NotAcceptable('can only have one layer')
  
  try:
    image: Image = Image.query.filter(Image.hash == manifest.content_json['layers'][0]['digest'].replace('sha256:', 'sha256.'), Image.container_ref == manifest.container_ref).one()
  except NoResultFound:
    current_app.logger.debug(f"image in manifest {manifest.content} not found")
    raise errors.NotFound("Image not found")
  
  if not image.uploaded:
    raise errors.NotAcceptable(f"Image not uploaded")
  
  return send_file(image.location, as_attachment=True, attachment_filename=fn)