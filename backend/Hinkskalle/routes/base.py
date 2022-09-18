from Hinkskalle import registry, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask import current_app, jsonify, make_response, request, redirect, g, send_from_directory
from werkzeug.security import safe_join 
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from werkzeug.datastructures import EnvironHeaders
import os
import re
from sqlalchemy import desc

from Hinkskalle.models import Tag, ContainerSchema
from .util import _get_service_url

@current_app.route('/', defaults={'path': ''})
@current_app.route('/<path:path>')
def frontend(path):
  orig_path=path
  if path.startswith('v1/') or path.startswith('v2/'):
    raise errors.NotFound
  if path=="" or not os.path.exists(safe_join(current_app.config.get('FRONTEND_PATH'), path)):  # type: ignore
    path="index.html"
  current_app.logger.debug(f"frontend route to {path} from {orig_path}")
  return send_from_directory(current_app.config.get('FRONTEND_PATH'), path) # type: ignore


class VersionSchema(Schema):
  version = fields.String()
  apiVersion = fields.String()

class VersionResponseSchema(ResponseSchema):
  data = fields.Nested(VersionSchema())

class ConfigParamsSchema(Schema):
  enable_register = fields.Boolean()
  singularity_flavor = fields.String()
  default_user_quota = fields.Integer()
  default_group_quota = fields.Integer()
  frontend_url = fields.String()

class ConfigResponseSchema(ResponseSchema):
  libraryAPI = fields.Dict()
  keystoreAPI = fields.Dict()
  tokenAPI = fields.Dict()
  params = fields.Nested(ConfigParamsSchema())

@registry.handles(
  rule='/version',
  method='GET',
  response_body_schema=VersionResponseSchema(),
  tags=['singularity']
)
def version():
  """https://singularityhub.github.io/library-api/#/spec/main?id=get-version"""
  return {
    'data': {
      'version': 'v1.0.0',
      'apiVersion': '2.0.0-alpha.2',
    }
  }

@registry.handles(
  rule='/assets/config/config.prod.json',
  method='GET',
  response_body_schema=ConfigResponseSchema(),
  tags=['singularity']
)
def config():
  """https://singularityhub.github.io/library-api/#/spec/main?id=get-version"""
  service_url = _get_service_url()
  return {
    'libraryAPI': {
      'uri': service_url
    },
    'keystoreAPI': {
      'uri': current_app.config.get('KEYSERVER_URL'),
    },
    'tokenAPI': {
      'uri': service_url
    },
    'params': {
      'enable_register': current_app.config.get('ENABLE_REGISTER'),
      'singularity_flavor': current_app.config.get('SINGULARITY_FLAVOR'),
      'default_user_quota': current_app.config.get('DEFAULT_USER_QUOTA'),
      'default_group_quota': current_app.config.get('DEFAULT_GROUP_QUOTA'),
      'frontend_url': current_app.config.get('FRONTEND_URL') if current_app.config.get('FRONTEND_URL') else service_url,
    }
  }

class LatestContainerSchema(Schema):
  tags = fields.List(fields.Dict())
  container = fields.Nested(ContainerSchema)

class LatestContainerListResponseSchema(ResponseSchema):
  data = fields.Nested(LatestContainerSchema, many=True)

@registry.handles(
  rule='/v1/latest',
  method='GET',
  response_body_schema=LatestContainerListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def latest_container():
  tags = Tag.query.order_by(desc(Tag.createdAt))
  ret = {}
  for tag in tags:
    if tag.container_ref.private and not tag.container_ref.check_access(g.authenticated_user):
      continue
    if not tag.container_ref.id in ret:
      #current_app.logger.debug(f"return image {tag.name}/{tag.image_ref.container_ref.name}")
      ret[tag.container_ref.id] = {
        'tags': [],
        'container': tag.container_ref,
      }
    ret[tag.container_ref.id]['tags'].append({
      'name': tag.name,
      'arch': tag.arch,
      'imageType': tag.image_ref.type if tag.image_id else None,
      'manifestType': tag.manifest_ref.type if tag.manifest_id else None,
    })
    if len(ret) >= 10:
      break

  return { 'data': list(ret.values()) }


@current_app.before_request
def before_request_func():
  # fake content type (singularity does not set it)
  if (request.path.startswith('/v1') or (request.path.startswith('/v2') and not request.path == '/v2/' and not request.path.startswith('/v2/__uploads') and not request.path.endswith('/blobs/uploads/'))) and (request.method=='POST' or request.method=='PUT'):
    request.headers.environ.update(CONTENT_TYPE='application/json') # type: ignore
  
  # redirect double slashes to /default/ (singularity client sends meaningful //)
  # only pull (/imagefile//) should not be redirected. For some reason
  # singularity pull uses a double slash there. Let the regular (werkzeug) // normalization
  # take care of that.
  if request.path.startswith('/v1') and re.search(r"(?<!imagefile)//", request.path):
    newpath = re.sub(r"(?<!imagefile)//", "/default/", request.path)
    return redirect(newpath, 308)

def create_error_object(code, msg):
  return [
    { 'title': 'Fail!', 'detail': msg, 'code': code }
  ]

@current_app.errorhandler(errors.Unauthorized)
def unauthorized(error):
  response = make_response(jsonify(status='error', errors=create_error_object(401, 'Not Authorized')), 401)
  response.headers['WWW-Authenticate']=f'bearer realm="{_get_service_url()}/v2/"'
  return response


@current_app.errorhandler(404)
def not_found(error):
  return make_response(jsonify(status='error', errors=create_error_object(404, 'Not found.')), 404)

@current_app.errorhandler(500)
def internal_error(error):
  current_app.logger.error(error)
  return make_response(jsonify(status='error', errors=create_error_object(500, str(error))), 500)

@current_app.errorhandler(403)
def forbidden_error(error):
  return make_response(jsonify(status="error", errors=create_error_object(403, str(error))), 403)

@current_app.errorhandler(400)
def bad_request_error(error):
  current_app.logger.error(error)
  return make_response(jsonify(status="error", errors=create_error_object(400, str(error))), 400)

@current_app.after_request
def add_header(r):
  r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  r.headers["Pragma"] = "no-cache"
  r.headers["Expires"] = "0"
  r.headers['Cache-Control'] = 'public, max-age=0'
  r.headers['Access-Control-Allow-Origin'] = '*'
  r.headers['Access-Control-Allow-Credentials'] = 'true'
  r.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
  r.headers['Access-Control-Allow-Methods'] = 'PUT, POST, GET, DELETE, OPTIONS'

  return r
