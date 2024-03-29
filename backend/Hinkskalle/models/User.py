from distutils import bcppcompiler
import typing
from Hinkskalle import db
import Hinkskalle.util.name_check
#from Hinkskalle.util.name_check import validate_as_name, validate_name
from marshmallow import fields, Schema, validates_schema, ValidationError
from datetime import datetime, timedelta
from flask import current_app, g
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from passlib.hash import sha512_crypt
import secrets
import base64

from ..util.schema import BaseSchema, LocalDateTime

user_stars = db.Table('user_stars', db.metadata,
  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
  db.Column('container_id', db.Integer, db.ForeignKey('container.id'), nullable=False),
  keep_existing=True,
)

class GroupRoles(enum.Enum):
  admin = 'admin'
  contributor = 'contributor'
  readonly = 'readonly'
  def __str__(self):
    return self.value

class PassKeySchema(Schema):
  id = fields.String(required=True, dump_only=True, attribute='encoded_id')
  name = fields.String(required=True)
  createdAt = fields.DateTime(dump_only=True)
  last_used = fields.DateTime(dump_only=True)
  current_sign_count = fields.Integer(dump_only=True)
  login_count = fields.Integer(dump_only=True)
  backed_up = fields.Boolean(dump_only=True)


class GroupSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  email = fields.String(required=True)
  description = fields.String(allow_none=True)
  quota = fields.Integer()
  used_quota = fields.Integer(dump_only=True)
  image_count = fields.Integer(dump_only=True)
  entityRef = fields.String(dump_only=True, allow_none=True, attribute='entity_ref')

  users = fields.List(fields.Nested('GroupMemberSchema'), dump_only=True)
  collections = fields.Integer(dump_only=True)

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

  canEdit = fields.Boolean(dump_only=True, default=False)

class UserSchema(BaseSchema):
  id = fields.String(required=True, dump_only=True)
  username = fields.String(required=True)
  email = fields.String(required=True)
  firstname = fields.String(required=True)
  lastname = fields.String(required=True)
  is_admin = fields.Boolean(data_key='isAdmin')
  is_active = fields.Boolean(data_key='isActive')
  password_disabled = fields.Boolean(data_key='passwordDisabled')
  source = fields.String()
  quota = fields.Integer()
  used_quota = fields.Integer(dump_only=True)
  image_count = fields.Integer(dump_only=True)

  groups = fields.List(fields.Nested('UserMemberSchema', allow_none=True), dump_only=True)

  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

  canEdit = fields.Boolean(dump_only=True, default=False)

  @validates_schema
  def validate_username(self, data, **kwargs):
    errors = Hinkskalle.util.name_check.validate_name(data, key='username')
    if errors:
      raise ValidationError(errors)


class UserMemberSchema(Schema):
  group = fields.Nested('GroupSchema', exclude=('users',))
  role = fields.String()

class GroupMemberSchema(Schema):
  user = fields.Nested('UserSchema', exclude=('groups',))
  role = fields.String()


class UserGroup(db.Model): # type: ignore
  user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
  group_id = db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
  role = db.Column('role', db.Enum(GroupRoles, name='group_roles'), default=GroupRoles.readonly.value, nullable=False)
  user = db.relationship('User', back_populates='groups')
  group = db.relationship('Group', back_populates='users')

class User(db.Model): # type: ignore
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(), unique=True, nullable=False)
  password = db.Column(db.String())
  email = db.Column(db.String(), unique=True, nullable=False)
  firstname = db.Column(db.String(), nullable=False)
  lastname = db.Column(db.String(), nullable=False)
  is_admin = db.Column(db.Boolean, default=False)
  is_active = db.Column(db.Boolean, default=True)
  quota = db.Column(db.BigInteger, default=lambda: current_app.config.get('DEFAULT_USER_QUOTA', 0))
  used_quota = db.Column(db.BigInteger, default=0)

  source = db.Column(db.String(), default='local', nullable=False)
  _passkey_id = db.Column('passkey_id', db.LargeBinary(16), default=lambda: secrets.token_bytes(16), unique=True)
  password_disabled = db.Column(db.Boolean, default=False, nullable=False)

  groups = db.relationship('UserGroup', back_populates='user', cascade='all, delete-orphan')
  tokens = db.relationship('Token', back_populates='user', cascade="all, delete-orphan")
  manual_tokens = db.relationship('Token', viewonly=True, primaryjoin="and_(User.id==Token.user_id, Token.source=='manual')")
  starred = db.relationship('Container', secondary=user_stars, back_populates='starred')
  starred_sth = db.relationship('Container', viewonly=True, secondary=user_stars, lazy='dynamic')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  entities = db.relationship('Entity', back_populates='owner')
  collections = db.relationship('Collection', back_populates='owner')
  containers = db.relationship('Container', back_populates='owner')
  images = db.relationship('Image', back_populates='owner')
  images_ref = db.relationship('Image', lazy='dynamic', viewonly=True)
  tags = db.relationship('Tag', back_populates='owner')
  uploads = db.relationship('ImageUploadUrl', back_populates='owner', cascade='all, delete-orphan')
  passkeys = db.relationship('PassKey', back_populates='user', cascade='all, delete-orphan')

  @validates('email')
  def convert_lower(self, key, value):
    return value.lower()

  @validates('username')
  def check_username(self, key, value):
    value = value.lower()
    Hinkskalle.util.name_check.validate_as_name(value)
    return value

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

  @property
  def passkey_id(self) -> str:
    return base64.b64encode(self._passkey_id).decode('utf-8')

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
  
  @property
  def image_count(self) -> int:
    return self._valid_images().count()

  def calculate_used(self) -> int:
    counted = {}
    total = 0
    for img in self._valid_images():
      if img.size is None:
        continue
      if not counted.get(img.location):
        counted[img.location] = True
        total += img.size
    self.used_quota = total
    return total

  def _valid_images(self):
    from Hinkskalle.models.Image import UploadStates
    return self.images_ref.filter_by(uploadState=UploadStates.completed)

  @property
  def canEdit(self) -> bool:
    return self.check_update_access(g.authenticated_user)

  def check_update_access(self, user) -> bool:
    if user.is_admin:
      return True
    elif self.id == user.id:
      return True
    else:
      return False
  

class PassKey(db.Model): # type: ignore
  id = db.Column(db.LargeBinary(16), primary_key=True)
  name = db.Column(db.String, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  public_key = db.Column(db.LargeBinary)
  backed_up = db.Column(db.Boolean, default=False)
  current_sign_count = db.Column(db.Integer, default=0, nullable=False)
  createdAt = db.Column(db.DateTime, default=datetime.now)

  last_used = db.Column(db.DateTime)
  login_count = db.Column(db.Integer, default=0)

  user = db.relationship('User', back_populates='passkeys')
  __table_args__ = (db.UniqueConstraint('user_id', 'name', name='pass_key_name_user_id_idx'), )

  @property
  def encoded_id(self):
    return base64.b64encode(self.id).decode('utf-8')


class Group(db.Model): # type: ignore
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), unique=True, nullable=False)
  email = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  quota = db.Column(db.BigInteger, default=lambda: current_app.config.get('DEFAULT_GROUP_QUOTA', 0))

  users = db.relationship('UserGroup', back_populates='group', cascade='all, delete-orphan')
  users_sth = db.relationship('UserGroup', viewonly=True, lazy='dynamic')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  entity = db.relationship('Entity', back_populates='group', uselist=False, cascade='all, delete-orphan')
  owner = db.relationship('User')

  @property
  def entity_ref(self) -> typing.Optional[str]:
    return self.entity.name if self.entity else None
  
  @property
  def collections(self) -> int:
    return self.entity.size if self.entity else 0

  def get_member(self, user: User) -> typing.Optional[UserGroup]:
    return self.users_sth.filter(UserGroup.user_id == user.id).first()
  
  def check_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    if self.owner == user:
      return True
    ug = self.get_member(user)
    if ug:
      return True
    return False

  @property
  def canEdit(self) -> bool:
    return self.check_update_access(g.authenticated_user)

  def check_update_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    if self.owner == user:
      return True
    ug = self.users_sth.filter(UserGroup.user_id == user.id).first()
    if ug and ug.role == GroupRoles.admin:
      return True
    return False

  @property
  def used_quota(self) -> int:
    if not self.entity:
      return 0
    return self.entity.used_quota

  @property
  def image_count(self) -> int:
    if not self.entity:
      return 0
    return self._valid_images().count()
    
  def calculate_used(self) -> int:
    if not self.entity:
      return 0
    return self.entity.calculate_used()
  
  def _valid_images(self):
    from Hinkskalle.models import Image, UploadStates, Container, Collection, Entity
    return Image.query.join(Container, Collection, Entity).filter(
      Entity.group==self,
      Image.uploadState==UploadStates.completed
    )


  


class TokenSchema(BaseSchema):
  id = fields.String(required=True, dump_only=True)
  generatedToken = fields.String(dump_only=True)
  key_uid = fields.String(required=True, dump_only=True)
  comment = fields.String(allow_none=True)

  user = fields.Nested('UserSchema')

  expiresAt = LocalDateTime(allow_none=True)
  source = fields.String(dump_only=True, allow_none=True)

  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

class Token(db.Model): # type: ignore
  id = db.Column(db.Integer, primary_key=True)
  _token = db.Column('token', db.String(), nullable=False)
  key_uid = db.Column(db.String(), unique=True, nullable=False)
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

  generatedToken: str

  @hybrid_property
  def token(self) -> str: # type: ignore
    return self._token
  
  @token.setter
  def token(self, upd: str):
    if upd and not upd.startswith('$'):
      self._token = sha512_crypt.hash(upd, rounds=10000)
      self.generatedToken = upd
      self.key_uid = upd[:12]
    else:
      self._token = upd
  
  def check_token(self, token: str) -> bool:
    if not self.token:
      current_app.logger.debug(f"Token {self.key_uid} token is NULL")
      return False
    try:
      result = sha512_crypt.verify(token, self._token)
    except Exception as err:
      current_app.logger.info(f"Token {self.key_uid}/{self.user.username} hash check failed: {err}")
      return False
    return result

  def refresh(self) -> None:
    self.expiresAt = datetime.now() + Token.defaultExpiration
