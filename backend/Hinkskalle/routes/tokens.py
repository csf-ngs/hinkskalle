from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
import datetime

from flask import current_app, g

from Hinkskalle.models import User, Token, TokenSchema

class TokenResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema)

class TokenListResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema, many=True)

class TokenCreateSchema(TokenSchema, RequestSchema):
  pass

class TokenUpdateSchema(TokenSchema, RequestSchema):
  pass

class TokenDeleteResponseSchema(ResponseSchema):
  status = fields.String()

def _get_user(username):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} does not exist...")
  
  if not user.check_token_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to tokens.")

  return user

@registry.handles(
  rule='/v1/users/<string:username>/tokens',
  method='GET',
  response_body_schema=TokenListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def list_tokens(username):
  user = _get_user(username)
  return { 'data': user.manual_tokens }

@registry.handles(
  rule='/v1/users/<string:username>/tokens',
  method='POST',
  response_body_schema=TokenResponseSchema(),
  request_body_schema=TokenCreateSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def create_tokens(username):
  body = rebar.validated_body
  user = _get_user(username)
  token = user.create_token(**body)
  token.source = 'manual'
  db.session.commit()
  return { 'data': token }

@registry.handles(
  rule='/v1/users/<string:username>/tokens/<int:token_id>',
  method='PUT',
  response_body_schema=TokenResponseSchema(),
  request_body_schema=TokenUpdateSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def update_token(username, token_id):
  body = rebar.validated_body
  user = _get_user(username)
  try:
    token = Token.query.filter(Token.id==token_id, Token.user_id==user.id).one()
  except NoResultFound:
    raise errors.NotFound(f"Invalid token id.")
  
  for key in body:
    setattr(token, key, body[key])
  token.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': token }

@registry.handles(
  rule='/v1/users/<string:username>/tokens/<int:token_id>',
  method='DELETE',
  response_body_schema=TokenDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def delete_token(username, token_id):
  user = _get_user(username)
  try:
    token = Token.query.filter(Token.id==token_id, Token.user_id==user.id).one()
  except NoResultFound:
    raise errors.NotFound(f"Invalid token id.")

  db.session.delete(token)
  db.session.commit()
  return { 'status': 'ok' }