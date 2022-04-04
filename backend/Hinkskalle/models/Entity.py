from asyncio.proactor_events import _ProactorBaseWritePipeTransport
from Hinkskalle import db
from marshmallow import fields, Schema, validates_schema, ValidationError
from datetime import datetime
from sqlalchemy.orm import validates
from flask import current_app
from Hinkskalle.util.name_check import validate_name
from Hinkskalle.models.User import User

class EntitySchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
  size = fields.Integer(dump_only=True)
  quota = fields.Integer()
  usedQuota = fields.Integer(dump_only=True, attribute='used_quota')
  defaultPrivate = fields.Boolean()
  customData = fields.String(allow_none=True)

  collections = fields.List(fields.String(), allow_none=True, dump_only=True)

  @validates_schema
  def validate_name(self, data, **kwargs):
    errors = validate_name(data)
    if errors:
      raise ValidationError(errors)

class Entity(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), unique=True, nullable=False)
  description = db.Column(db.String())
  customData = db.Column(db.String())

  defaultPrivate = db.Column(db.Boolean, default=False)
  quota= db.Column(db.BigInteger, default=lambda: current_app.config.get('DEFAULT_USER_QUOTA', 0))
  used_quota= db.Column(db.BigInteger, default=0)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  owner = db.relationship('User', back_populates='entities')

  collections_ref = db.relationship('Collection', back_populates='entity_ref', lazy='dynamic')

  @validates('name')
  def convert_lower(self, key, value: str) -> str:
    return value.lower()


  @property
  def size(self) -> int:
    return self.collections_ref.count()

  def calculate_used(self) -> int:
    entity_size = 0
    counted = {}
    # naive implementation. could be faster if we let
    # the db do the heavy lifiting. let's see.
    for collection in self.collections_ref:
      collection_size = 0
      collection_counted = {}
      for container in collection.containers_ref:
        container_size = 0
        container_counted = {}
        for img in container.images_ref:
          if not img.uploaded or img.size is None:
            continue
          if not counted.get(img.location):
            counted[img.location]=True
            entity_size += img.size
          if not container_counted.get(img.location):
            container_counted[img.location]=True
            container_size += img.size
          if not collection_counted.get(img.location):
            collection_counted[img.location]=True
            collection_size += img.size
        container.used_quota = container_size
      collection.used_quota=collection_size
    self.used_quota=entity_size
    return entity_size

  def check_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    elif self.name == 'default':
      return True
    else:
      return False
  
  def check_update_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return False

