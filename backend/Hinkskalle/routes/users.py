from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from flask import request, current_app, g

from Hinkskalle.models import UserSchema, User

import datetime

class UserResponseSchema(ResponseSchema):
  data = fields.Nested(UserSchema)

class UserListResponseSchema(ResponseSchema):
  data = fields.Nested(UserSchema, many=True)

class UserCreateSchema(UserSchema, RequestSchema):
  pass

class UserUpdateSchema(UserSchema, RequestSchema):
  pass

class UserDeleteResponseSchema(ResponseSchema):
  stats = fields.String()

@registry.handles(
  rule='/v1/users',
  method='GET',
  response_body_schema=UserListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def list_users():
  objs = User.query.all()
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='GET',
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def get_user(username):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  if not user.check_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user.")
  return { 'data': user }

@registry.handles(
  rule='/v1/users',
  method='POST',
  request_body_schema=UserCreateSchema(),
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin)
)
def create_user():
  body = rebar.validated_body
  body.pop('id', None)

  new_user = User(**body)
  new_user.createdBy = g.authenticated_user.username

  try:
    db.session.add(new_user)
    db.session.commit()
  except IntegrityError as err:
    current_app.logger.error(err)
    raise errors.PreconditionFailed(f"User {new_user.username} already exists")

  return { 'data': new_user }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='PUT',
  request_body_schema=UserUpdateSchema(),
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def update_user(username):
  body = rebar.validated_body

  try:
    user = User.query.filter(User.username==username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  
  if not user.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user")

  if not g.authenticated_user.is_admin:
    if body.get('source', user.source) != user.source:
      raise errors.Forbidden("Cannot change source field")
    if body.get('is_admin', user.is_admin) != user.is_admin:
      raise errors.Forbidden("Cannot change isAdmin field")
    if body.get('is_active', user.is_active) != user.is_active:
      raise errors.Forbidden("Cannot change isActive field")
  
  for key in body:
    setattr(user, key, body[key])
  user.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': user }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='DELETE',
  response_body_schema=UserDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin),
)
def delete_user(username):
  try:
    user = User.query.filter(User.username==username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")

  db.session.delete(user)
  db.session.commit()

  return { 'status': 'ok' }
