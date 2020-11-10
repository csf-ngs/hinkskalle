from Hinkskalle import registry, password_checkers, authenticator, rebar, db
from Hinkskalle.models import TokenSchema, User, Token
from Hinkskalle.util.auth.token import Scopes
from Hinkskalle.util.auth.exceptions import UserNotFound, UserDisabled, InvalidPassword
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import current_app, g

import datetime

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
    user = password_checkers.check_password(body['username'], body['password'])
  except (UserNotFound, UserDisabled, InvalidPassword) as err:
    raise errors.Unauthorized(err.message)

  token = user.create_token()
  token.expiresAt = datetime.datetime.now() + datetime.timedelta(days=1)
  token.source = 'auto'
  db.session.add(token)
  db.session.commit()
  return { 'data': token }

