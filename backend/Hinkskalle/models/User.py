from Hinkskalle import db
from marshmallow import fields, Schema
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.orm import validates

from passlib.hash import sha512_crypt
import secrets

from ..util.schema import BaseSchema, LocalDateTime

user_stars = db.Table('user_stars', db.metadata,
  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
  db.Column('container_id', db.Integer, db.ForeignKey('container.id'), nullable=False),
)

user_groups_table = db.Table('users_groups', db.metadata,
  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
  db.Column('group_id', db.Integer, db.ForeignKey('group.id'), nullable=False),
)

class UserSchema(LocalSchema):
  id = fields.String(required=True, dump_only=True)
  username = fields.String(required=True)
  email = fields.String(required=True)
  firstname = fields.String(required=True)
  lastname = fields.String(required=True)
  is_admin = fields.Boolean(data_key='isAdmin')
  is_active = fields.Boolean(data_key='isActive')
  source = fields.String()

  groups = fields.List(fields.Nested('GroupSchema', allow_none=True, exclude=('users', )))

  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)


class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(), unique=True, nullable=False)
  password = db.Column(db.String())
  email = db.Column(db.String(), unique=True, nullable=False)
  firstname = db.Column(db.String(), nullable=False)
  lastname = db.Column(db.String(), nullable=False)
  is_admin = db.Column(db.Boolean, default=False)
  is_active = db.Column(db.Boolean, default=True)
  source = db.Column(db.String(), default='local', nullable=False)

  groups = db.relationship('Group', secondary=user_groups_table, back_populates='users')
  tokens = db.relationship('Token', back_populates='user', cascade="all, delete-orphan")
  manual_tokens = db.relationship('Token', viewonly=True, primaryjoin="and_(User.id==Token.user_id, Token.source=='manual')")
  starred = db.relationship('Container', secondary=user_stars, back_populates='starred')
  starred_sth = db.relationship('Container', viewonly=True, secondary=user_stars, lazy='dynamic')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)

  entities = db.relationship('Entity', back_populates='owner')
  collections = db.relationship('Collection', back_populates='owner')
  containers = db.relationship('Container', back_populates='owner')
  images = db.relationship('Image', back_populates='owner')
  tags = db.relationship('Tag', back_populates='owner')
  uploads = db.relationship('ImageUploadUrl', back_populates='owner', cascade='all, delete-orphan')

  @validates('username', 'email')
  def convert_lower(self, key, value):
    return value.lower()

  def create_token(self, **attrs):
    token = Token(token=secrets.token_urlsafe(48), **attrs)
    self.tokens.append(token)
    db.session.commit()
    return token
  
  def set_password(self, pw: str) -> None:
    self.password = sha512_crypt.hash(pw)
  
  def check_password(self, pw: str) -> bool:
    if not self.password:
      current_app.logger.debug(f"User {self.username} password is NULL")
      return False
    try:
      result = sha512_crypt.verify(pw, self.password)
    except Exception as err:
      current_app.logger.debug(f"User {self.username} hash check failed: {err}")
      return False
    return result

  def check_access(self, user) -> bool:
    return True
  
  def check_token_access(self, user) -> bool:
    if user.is_admin:
      return True
    if self.id == user.id:
      return True
    else:
      return False
  
  def check_sub_access(self, user) -> bool:
    if user.is_admin:
      return True
    elif self.id == user.id:
      return True
    else:
      return False

  def check_update_access(self, user) -> bool:
    if user.is_admin:
      return True
    elif self.id == user.id:
      return True
    else:
      return False


class GroupSchema(BaseSchema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  email = fields.String(required=True)

  users = fields.List(fields.Nested('UserSchema', allow_none=True, exclude=('groups', )))

  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
  

class Group(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), unique=True, nullable=False)
  email = db.Column(db.String(), unique=True, nullable=False)

  users = db.relationship('User', secondary=user_groups_table, back_populates='groups')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)

class TokenSchema(BaseSchema):
  id = fields.String(required=True, dump_only=True)
  token = fields.String(required=True, dump_only=True)
  comment = fields.String(allow_none=True)

  user = fields.Nested('UserSchema')

  expiresAt = LocalDateTime(allow_none=True)
  source = fields.String(dump_only=True, allow_none=True)

  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

class Token(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  token = db.Column(db.String(), unique=True, nullable=False)
  comment = db.Column(db.String())
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  expiresAt = db.Column(db.DateTime)
  source = db.Column(db.Enum('auto', 'manual', name="token_source_types"))

  user = db.relationship('User', back_populates='tokens')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deleted = db.Column(db.Boolean, default=False)

  defaultExpiration = timedelta(days=1)

  def refresh(self) -> None:
    self.expiresAt = datetime.now() + Token.defaultExpiration
