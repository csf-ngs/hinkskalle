from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound

from flask import current_app, g

from Hinkskalle.models import User, Token, TokenSchema

class TokenResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema)

class TokenListResponseSchema(ResponseSchema):
  data = fields.Nested(TokenSchema, many=True)

class TokenCreateSchema(RequestSchema):
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
  return { 'data': user.tokens }

@registry.handles(
  rule='/v1/users/<string:username>/tokens',
  method='POST',
  response_body_schema=TokenResponseSchema(),
  request_body_schema=TokenCreateSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def create_tokens(username):
  user = _get_user(username)
  token = user.create_token()
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