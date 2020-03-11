from Hinkskalle import db
from marshmallow import fields, Schema
from datetime import datetime

from passlib.hash import sha512_crypt

user_groups_table = db.Table('users_groups', db.metadata,
  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
  db.Column('group_id', db.Integer, db.ForeignKey('group.id'), nullable=False),
)

class UserSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  username = fields.String(required=True)
  email = fields.String(required=True)
  firstname = fields.String()
  lastname = fields.String()
  is_admin = fields.Boolean(load_from='isAdmin', dump_to='isAdmin')

  groups = fields.List(fields.Nested('GroupSchema', allow_none=True, exclude=('users', )))

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
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

  groups = db.relationship('Group', secondary=user_groups_table, back_populates='users')
  tokens = db.relationship('Token', back_populates='user')

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)

  entities = db.relationship('Entity', back_populates='owner')
  collections = db.relationship('Collection', back_populates='owner')
  containers = db.relationship('Container', back_populates='owner')
  images = db.relationship('Image', back_populates='owner')
  tags = db.relationship('Tag', back_populates='owner')

  def set_password(self, pw):
    self.password = sha512_crypt.hash(pw)
  
  def check_password(self, pw):
    return sha512_crypt.verify(pw, self.password)

class GroupSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  email = fields.String(required=True)

  users = fields.List(fields.Nested('UserSchema', allow_none=True, exclude=('groups', )))

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
  

class Group(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), unique=True, nullable=False)
  email = db.Column(db.String(), unique=True, nullable=False)

  users = db.relationship('User', secondary=user_groups_table, back_populates='groups')

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)

class TokenSchema(Schema):
  id = fields.String(required=True, dump_only=True)

  user = fields.Nested('UserSchema')

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

class Token(db.Model):
  id = db.Column(db.String(), primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  user = db.relationship('User', back_populates='tokens')

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
