from flask.helpers import make_response
from Hinkskalle import registry, password_checkers, authenticator, rebar, db
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.User import TokenSchema, UserSchema, PassKey, PassKeySchema
from Hinkskalle.util.auth.token import Scopes
from Hinkskalle.util.auth.exceptions import UserNotFound, UserDisabled, InvalidPassword
from Hinkskalle.util.auth.webauthn import AuthenticatorData
from Hinkskalle.routes.util import _get_service_url
from .util import _get_service_url
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import current_app, g, session
from sqlalchemy.orm.exc import NoResultFound # type: ignore
from sqlalchemy.exc import IntegrityError
import jwt
from calendar import timegm
from urllib.parse import urlparse
import json

from webauthn.registration.generate_registration_options import generate_registration_options
from webauthn.registration.verify_registration_response import verify_registration_response
from webauthn.helpers.options_to_json import options_to_json
from webauthn.helpers.base64url_to_bytes import base64url_to_bytes
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, RegistrationCredential

from datetime import datetime

class GetTokenRequestSchema(RequestSchema):
  username = fields.String(required=True)
  password = fields.String(required=True)

class TokenStatusResponseSchema(ResponseSchema):
  data = fields.Nested(UserSchema)
  status = fields.String()

class GetTokenResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema)

class RegisterCredentialResponseSchema(ResponseSchema):
  data = fields.Nested(PassKeySchema)

class GetDownloadTokenSchema(RequestSchema):
  type = fields.String(required=True)
  id = fields.String(required=True)
  username = fields.String(required=False)
  exp = fields.Integer(required=False)

class RegisterCredentialSchema(RequestSchema):
  name = fields.String(required=True)
  credential = fields.Dict()
  public_key = fields.String()

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
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def get_authn_create_options():
  rp_id = _get_rp_id()
  
  opts = generate_registration_options(
    rp_id=rp_id, # type: ignore
    rp_name='Hinkskalle',
    user_id=g.authenticated_user.passkey_id,
    user_name=g.authenticated_user.username,
    user_display_name=f"{g.authenticated_user.firstname} {g.authenticated_user.lastname}",
    exclude_credentials=[
      PublicKeyCredentialDescriptor(id=key.id) for key in g.authenticated_user.passkeys
    ],
    timeout=180000,
  )
  session['expected_challenge'] = opts.challenge
  current_app.logger.debug(session)

  return { 'data': { 'publicKey': json.loads(options_to_json(opts)) }}

@registry.handles(
  rule='/v1/webauthn/register',
  method='POST',
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  request_body_schema=RegisterCredentialSchema(),
  response_body_schema=RegisterCredentialResponseSchema(),
  tags=['hinkskalle-ext']
)
def authn_register():
  data = rebar.validated_body
  key = PassKey(user=g.authenticated_user, name=data['name'])
  credential = RegistrationCredential.parse_raw(json.dumps(data['credential']))

  verify_results = verify_registration_response(
    credential=credential,
    expected_challenge=session.pop('expected_challenge', None),
    expected_rp_id=_get_rp_id(),
    expected_origin=_get_origin(),
  )
  key.id = verify_results.credential_id
  key.public_key_spi = base64url_to_bytes(data['public_key'])

  #authData = AuthenticatorData(base64url_to_bytes(data['authenticator_data']))
  #key.id = authData.credential_id

  try:
    db.session.add(key)
    db.session.commit()
  except IntegrityError:
    raise errors.PreconditionFailed(f"key with name {key.name} already exists")


  return { 'data': key }


def _get_rp_id() -> str:
  if current_app.config['FRONTEND_URL']:
    rp_id = urlparse(current_app.config['FRONTEND_URL']).hostname
  else:
    rp_id = urlparse(_get_service_url()).hostname
  if not rp_id:
    raise errors.InternalError("could not determine rp_id")
  return rp_id

def _get_origin() -> str:
  if current_app.config['FRONTEND_URL']:
    origin = urlparse(current_app.config['FRONTEND_URL'])
  else:
    origin = urlparse(_get_service_url())
  return origin.geturl()
  
