from Hinkskalle import registry, fsk_auth, db
from flask import current_app, jsonify, make_response, request, redirect, g
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from werkzeug.datastructures import EnvironHeaders
import os
import re
from sqlalchemy import desc

from Hinkskalle.models import Tag, ContainerSchema

class VersionResponseSchema(ResponseSchema):
  version = fields.String()
  apiVersion = fields.String()

class ConfigResponseSchema(ResponseSchema):
  libraryAPI = fields.Dict()
  keystoreAPI = fields.Dict()
  tokenAPI = fields.Dict()

@registry.handles(
  rule='/version',
  method='GET',
  response_body_schema=VersionResponseSchema()
)
def version():
  return {
    'version': '2.0.0',
    'apiVersion': '2.0.0',
  }

@registry.handles(
  rule='/assets/config/config.prod.json',
  method='GET',
  response_body_schema=ConfigResponseSchema()
)
def config():
  service_url = request.url_root.rstrip('/')
  if current_app.config.get('PREFERRED_URL_SCHEME', 'http') == 'https':
    service_url = service_url.replace('http:', 'https:')
  return {
    'libraryAPI': {
      'uri': service_url
    },
    'keystoreAPI': {
      'uri': service_url
    },
    'tokenAPI': {
      'uri': service_url
    }
  }

class LatestContainerSchema(Schema):
  tags = fields.List(fields.String())
  container = fields.Nested(ContainerSchema)

class LatestContainerListResponseSchema(ResponseSchema):
  data = fields.Nested(LatestContainerSchema, many=True)

@registry.handles(
  rule='/v1/latest',
  method='GET',
  response_body_schema=LatestContainerListResponseSchema(),
  authenticators=fsk_auth,
)
def latest_container():
  tags = Tag.query.order_by(desc(Tag.createdAt))
  ret = {}
  for tag in tags:
    if not tag.image_ref.check_access(g.fsk_user):
      continue
    if not tag.image_ref.container_ref.id in ret:
      #current_app.logger.debug(f"return image {tag.name}/{tag.image_ref.container_ref.name}")
      ret[tag.image_ref.container_ref.id] = {
        'tags': [],
        'container': tag.image_ref.container_ref,
      }
    ret[tag.image_ref.container_ref.id]['tags'].append(tag.name)
    if len(ret) >= 10:
      break

  return { 'data': list(ret.values()) }


@current_app.before_request
def before_request_func():
  # fake content type (singularity does not set it)
  if request.path.startswith('/v1') and request.method=='POST':
    request.headers.environ.update(CONTENT_TYPE='application/json')
  
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
