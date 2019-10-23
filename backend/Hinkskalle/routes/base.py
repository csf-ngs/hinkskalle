from Hinkskalle import registry
from flask import current_app, jsonify, make_response, request
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from werkzeug.datastructures import EnvironHeaders
import os

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
  return {
    'libraryAPI': {
      'uri': request.url_root.rstrip('/') 
    },
    'keystoreAPI': {
      'uri': request.url_root.rstrip('/')
    },
    'tokenAPI': {
      'uri': request.url_root.rstrip('/')
    }
  }

# super hacky fake content type (singularity does not set it)
# header props are read-only (go figure) 
# change original WSGI environ dict (which is accessible)
# and reset headers (this field is not immutable, go figure some more)
@current_app.before_request
def before_request_func():
  if request.path.startswith('/v1') and request.method=='POST':
    request.headers.environ['CONTENT_TYPE']='application/json'
    request.headers = EnvironHeaders(request.headers.environ)

def create_error_object(code, msg):
  return [
    { 'title': 'Fail!', 'detail': msg, 'code': code }
  ]

@current_app.errorhandler(404)
def not_found(error):
  return make_response(jsonify(status='error', errors=create_error_object(404, 'Not found.')), 404)

@current_app.errorhandler(500)
def internal_error(error):
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
  return r