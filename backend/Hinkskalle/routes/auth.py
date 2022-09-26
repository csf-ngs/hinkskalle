from flask.helpers import make_response
from Hinkskalle import registry, password_checkers, authenticator, rebar, db
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.User import TokenSchema, UserSchema
from Hinkskalle.util.auth.token import Scopes
from Hinkskalle.util.auth.exceptions import UserNotFound, UserDisabled, InvalidPassword
from Hinkskalle.routes.util import _get_service_url
from .util import _get_service_url
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import current_app, g, request
from sqlalchemy.orm.exc import NoResultFound # type: ignore
import jwt
from calendar import timegm
from urllib.parse import urlparse
import base64
import re

from datetime import datetime

class GetTokenRequestSchema(RequestSchema):
  username = fields.String(required=True)
  password = fields.String(required=True)

class TokenStatusResponseSchema(ResponseSchema):
  data = fields.Nested(UserSchema)
  status = fields.String()

class GetTokenResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema)

class GetDownloadTokenSchema(RequestSchema):
  type = fields.String(required=True)
  id = fields.String(required=True)
  username = fields.String(required=False)
  exp = fields.Integer(required=False)

@registry.handles(
  rule='/v1/token-status',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  response_body_schema=TokenStatusResponseSchema(),
  tags=['singularity']
)
def token_status():
  """https://singularityhub.github.io/library-api/#/spec/main?id=get-v1token-status"""
  return {
    'status': 'welcome',
    'data': g.authenticated_user
  }

@registry.handles(
  rule='/v1/get-token',
  method='POST',
  request_body_schema=GetTokenRequestSchema(),
  response_body_schema=GetTokenResponseSchema(),
  tags=['hinkskalle-ext'],
)
def get_token():
  body = rebar.validated_body
  try:
    user = password_checkers.check_password(body['username'], body['password'])
  except (UserNotFound, UserDisabled, InvalidPassword) as err:
    raise errors.Unauthorized(err.message)

  
  try:
    user_entity = Entity.query.filter(Entity.name==user.username).one()
  except NoResultFound:
    user_entity = Entity(name=user.username, createdBy=user.username)
    db.session.add(user_entity)

  token = user.create_token()
  token.refresh()
  token.source = 'auto'
  db.session.add(token)
  db.session.commit()
  return { 'data': token }


@registry.handles(
  rule='/v1/get-download-token',
  method='POST',
  request_body_schema=GetDownloadTokenSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext'],
)
def get_download_token():
  data = rebar.validated_body
  if not g.authenticated_user.is_admin:
    if data.get('exp') or data.get('username'):
      raise errors.Forbidden(f"cannot override username and expiration date")

  if data['type'] == 'manifest':
    encoded_jwt = jwt.encode({ 
      'id': data['id'],
      'type': 'manifest',
      'username': data.get('username', g.authenticated_user.username),
      'exp': data.get('exp', timegm(datetime.utcnow().utctimetuple())+current_app.config['DOWNLOAD_TOKEN_EXPIRATION']),
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    target = f"{_get_service_url()}/v1/manifests/{data['id']}/download?temp_token={encoded_jwt}"
  else:
    raise errors.NotAcceptable('Invalid type')
  response = make_response({'location': target }, 202)
  response.headers['Location']=target
  return response
  

@registry.handles(
  rule='/v1/webauthn/create-options',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user),
  tags=['hinkskalle-ext']
)
def get_authn_create_options():
  if current_app.config['FRONTEND_URL']:
    rp_id = urlparse(current_app.config['FRONTEND_URL']).hostname
  else:
    rp_id = urlparse(_get_service_url()).hostname

  opts = {
    'publicKey': {
      'rp': {
        'id': rp_id,
        'name': "Hinkskalle",
      },
      'user': {
        'id': g.authenticated_user.passkey_id, #Uint8Array.from(atob('Vg4vHxiHQnPapKRD4+EIcw=='), c => c.charCodeAt(0)),
        'name': g.authenticated_user.username,
        'displayName': f"{g.authenticated_user.firstname} {g.authenticated_user.lastname}",
      },
      'excludeCredentials': [
        { 'type': 'public-key', 'id': base64.b64encode(key.id).decode('utf-8') } for key in g.authenticated_user.passkeys
      ], # XXX
      'pubKeyCredParams': [{
          'type': "public-key",
          'alg': -7
        }, {
          'type': "public-key",
          'alg': -257
        }
      ],
      'challenge': base64.b64encode(b'\0').decode('utf-8'), #,new Uint8Array([0]),
      'authenticatorSelection': {
        'authenticatorAttachment': "cross-platform",
        'userVerification': "discouraged",
        'requireResidentKey': False,
      },
      'timeout': 180000,
    }
  }
  return { 'data': opts }

