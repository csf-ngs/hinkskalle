from Hinkskalle import registry, authenticator, rebar, db
from Hinkskalle.models import TokenSchema, User, Token
from Hinkskalle.util.auth import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import current_app, g
import secrets

class TokenResponseSchema(ResponseSchema):
  status = fields.String()

class GetTokenRequestSchema(RequestSchema):
  username = fields.String(required=True)
  password = fields.String(required=True)

class GetTokenResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema)

@registry.handles(
  rule='/v1/token-status',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user),
  response_body_schema=TokenResponseSchema(),
)
def token_status():
  return {
    'status': 'welcome'
  }

@registry.handles(
  rule='/v1/get-token',
  method='POST',
  request_body_schema=GetTokenRequestSchema(),
  response_body_schema=GetTokenResponseSchema(),
)
def get_token():
  body = rebar.validated_body
  try:
    user = User.query.filter(User.username==body['username']).one()
  except:
    raise errors.Unauthorized("Username not found.")

  if not user.is_active:
    raise errors.Unauthorized("User is disabled.")
  
  if not user.check_password(body['password']):
    raise errors.Unauthorized("Invalid password.")

  g.authenticated_user = user
  token = Token(id=secrets.token_urlsafe(48), user=user)
  db.session.add(token)
  db.session.commit()
  return { 'data': token }

