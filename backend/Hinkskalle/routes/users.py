from ast import Pass
import base64
from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound # type: ignore
from sqlalchemy.exc import IntegrityError
from flask import current_app, g

from Hinkskalle.models import UserSchema, User, ContainerSchema, Container, Entity, PassKey, PassKeySchema

import datetime

# use Schema here instead of flask_rebar's ResponseSchema
# ResponseSchema switches on validation on dump, which would
# throw exceptions on legacy usernames
class UserResponseSchema(Schema):
  data = fields.Nested(UserSchema)

class UserListResponseSchema(Schema):
  data = fields.Nested(UserSchema, many=True)

class UserRegisterSchema(RequestSchema):
  username = fields.String(required=True)
  email = fields.String(required=True)
  firstname = fields.String(required=True)
  lastname = fields.String(required=True)
  password = fields.String(required=True)

class UserCreateSchema(UserSchema, RequestSchema):
  password = fields.String()

class UserStarsResponseSchema(ResponseSchema):
  data = fields.Nested(ContainerSchema, many=True)

class UserSearchQuerySchema(RequestSchema):
  username = fields.String(required=False)

# taken from https://flask-rebar.readthedocs.io/en/latest/recipes.html#marshmallow-partial-schemas
# to allow partial updates
class UserUpdateSchema(UserSchema, RequestSchema):
  password = fields.String(required=False)
  oldPassword = fields.String(required=False)
  def __init__(self, **kwargs):
    super_kwargs = dict(kwargs)
    partial_arg = super_kwargs.pop('partial', True)
    super(UserUpdateSchema, self).__init__(partial=partial_arg, **super_kwargs)

class UserDeleteResponseSchema(ResponseSchema):
  status = fields.String()

class PassKeyListResponseSchema(ResponseSchema):
  data = fields.Nested(PassKeySchema, many=True)

class PassKeyDeleteResponseSchema(ResponseSchema):
  status = fields.String()

@registry.handles(
  rule='/v1/users',
  method='GET',
  response_body_schema=UserListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  query_string_schema=UserSearchQuerySchema(),
  tags=['hinkskalle-ext']
)
def list_users():
  args = rebar.validated_args
  search = []
  if args.get('username', None):
    search.append(User.username.ilike(f"%{args['username']}%"))
  objs = User.query.filter(*search)
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='GET',
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
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
  rule='/v1/users/<string:username>/stars',
  method='GET',
  response_body_schema=UserStarsResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def get_stars(username):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  if not user.check_sub_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user.")
  containers = [ c for c in user.starred if c.check_access(g.authenticated_user) ]
  return { 'data': containers }

@registry.handles(
  rule='/v1/users/<string:username>/stars/<string:container_id>',
  method='POST',
  response_body_schema=UserStarsResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def add_star(username, container_id):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  if not user.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user.")

  try:
    container = Container.query.filter(Container.id == container_id).one()
  except NoResultFound:
    raise errors.NotFound(f"container {container_id} not found")
  if not container.check_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to container.")

  user.starred.append(container)
  db.session.commit()
  containers = [ c for c in user.starred if c.check_access(g.authenticated_user) ]
  return { 'data': containers }

@registry.handles(
  rule='/v1/users/<string:username>/stars/<string:container_id>',
  method='DELETE',
  response_body_schema=UserStarsResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def remove_star(username, container_id):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  if not user.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user.")

  try:
    container = user.starred_sth.filter(Container.id==container_id).one()
  except NoResultFound:
    raise errors.NotFound(f"container {container_id} not found")

  user.starred.remove(container)
  db.session.commit()
  containers = [ c for c in user.starred if c.check_access(g.authenticated_user) ]
  return { 'data': containers }

def _create_user(body, password=None):
  new_user = User(**body)
  if password:
    new_user.set_password(password)
  if 'authenticated_user' in g:
    new_user.createdBy=g.authenticated_user.username

  entity = Entity(name=new_user.username, owner=new_user)
  try:
    db.session.add(new_user)
    db.session.add(entity)
    db.session.commit()
  except IntegrityError as err:
    msg = f"User {new_user.username} already exists (email and/or username already taken" if err.statement.find('entity') == -1  else f"entity {new_user.username} already exists"
    raise errors.PreconditionFailed(msg)
  return new_user

@registry.handles(
  rule='/v1/register',
  method='POST',
  request_body_schema=UserRegisterSchema(),
  response_body_schema=UserResponseSchema(),
  tags=['hinkskalle-ext']
)
def register_account():
  if not current_app.config.get('ENABLE_REGISTER', False):
    raise errors.Forbidden(f"Registration is disabled.")

  body = rebar.validated_body
  new_user = _create_user(body, body.pop('password'))

  return { 'data': new_user }


@registry.handles(
  rule='/v1/users',
  method='POST',
  request_body_schema=UserCreateSchema(),
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin), # type: ignore
  tags=['hinkskalle-ext']
)
def create_user():
  body = rebar.validated_body
  body.pop('id', None)
  new_user = _create_user(body, body.pop('password', None))

  return { 'data': new_user }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='PUT',
  request_body_schema=UserUpdateSchema(),
  response_body_schema=UserResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def update_user(username):
  body = rebar.validated_body

  try:
    user = User.query.filter(User.username==username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")
  
  if not user.check_update_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to user")

  if user.source != 'local':
    body = {k:v for k, v in body.items() if k in ['is_admin', 'is_active', 'source', 'quota', 'password_disabled']}

  if not g.authenticated_user.is_admin:
    body.pop('quota', None)
    if body.get('source', user.source) != user.source:
      raise errors.Forbidden("Cannot change source field")
    if body.get('is_admin', user.is_admin) != user.is_admin:
      raise errors.Forbidden("Cannot change isAdmin field")
    if body.get('is_active', user.is_active) != user.is_active:
      raise errors.Forbidden("Cannot change isActive field")
    if body.get('password'):
      try:
        oldPw = body.pop('oldPassword')
      except KeyError:
        raise errors.PreconditionFailed("Old password required")
      if not user.check_password(oldPw):
        raise errors.Forbidden('Old password incorrect')
  
  new_password = body.pop('password', None)
  
  for key in body:
    setattr(user, key, body[key])
  user.updatedAt = datetime.datetime.now()
  if new_password:
    user.set_password(new_password)
  
  with db.session.no_autoflush: # type: ignore
    if username != user.username:
      try:
        entity = Entity.query.filter(Entity.name==username).one()
        if entity.createdBy != username:
          raise errors.PreconditionFailed(f"Cannot rename entity {entity.name}, not owned by user")
        entity.name=user.username
      except NoResultFound:
        pass

  try:
    db.session.commit()
  except IntegrityError as err:
    raise errors.Conflict(f"Cannot change username, new name already taken")


  return { 'data': user }

@registry.handles(
  rule='/v1/users/<string:username>',
  method='DELETE',
  response_body_schema=UserDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.admin), # type: ignore
  tags=['hinkskalle-ext']
)
def delete_user(username):
  try:
    user = User.query.filter(User.username==username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} not found")

  db.session.delete(user)
  db.session.commit()

  return { 'status': 'ok' }

@registry.handles(
  rule='/v1/users/<string:username>/passkeys',
  method='GET',
  response_body_schema=PassKeyListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext']
)
def list_passkeys(username):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} does not exist...")
  
  # reuse token access rules here
  if not user.check_token_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to tokens.")

  return { 'data': user.passkeys }

@registry.handles(
  rule='/v1/users/<string:username>/passkeys/<path:passkey_id>',
  method='DELETE',
  response_body_schema=PassKeyDeleteResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
  tags=['hinkskalle-ext'],
)
def delete_passkey(username, passkey_id):
  try:
    user = User.query.filter(User.username == username).one()
  except NoResultFound:
    raise errors.NotFound(f"user {username} does not exist...")
  
  # reuse token access rules here
  if not user.check_token_access(g.authenticated_user):
    raise errors.Forbidden("Access denied to tokens.")
  
  passkey = PassKey.query.filter(PassKey.id==base64.b64decode(passkey_id), PassKey.user==user).first()
  if not passkey:
    raise errors.NotFound(f'Passkey with id {passkey_id} not found')
  db.session.delete(passkey)
  db.session.commit()
  return { 'status': 'ok' }

