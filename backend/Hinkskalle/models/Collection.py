from Hinkskalle import db
from marshmallow import Schema, fields, validates_schema, ValidationError
from ..util.schema import BaseSchema, LocalDateTime
from datetime import datetime
from sqlalchemy.orm import validates
from Hinkskalle.util.name_check import validate_name
from flask import g

from Hinkskalle.models.User import GroupRoles, User

class CollectionSchema(BaseSchema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(allow_none=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
  size = fields.Integer(dump_only=True)
  private = fields.Boolean()
  customData = fields.String(allow_none=True)
  usedQuota = fields.Integer(dump_only=True, attribute='used_quota')

  entity = fields.String(required=True)
  entityName = fields.String(dump_only=True)

  containers = fields.List(fields.String(), allow_none=True, dump_only=True)

  canEdit = fields.Boolean(dump_only=True, default=False)

  @validates_schema
  def validate_name(self, data, **kwargs):
    errors = validate_name(data)
    if errors:
      raise ValidationError(errors)


class Collection(db.Model): # type: ignore
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  customData = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)
  used_quota = db.Column(db.BigInteger(), default=0)

  entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  entity_ref = db.relationship('Entity', back_populates='collections_ref')
  containers_ref = db.relationship('Container', back_populates='collection_ref', lazy='dynamic')
  owner = db.relationship('User', back_populates='collections')

  @validates('name')
  def convert_lower(self, key, value) -> str:
    return value.lower()

  __table_args__ = (db.UniqueConstraint('name', 'entity_id', name='name_entity_id_idx'),)

  @property
  def size(self) -> int:
    return self.containers_ref.count()

  @property
  def entity(self) -> int:
    return self.entity_ref.id
  @property
  def entityName(self) -> str:
    return self.entity_ref.name
  
  def check_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return self.entity_ref.check_access(user)
  
  @property
  def canEdit(self) -> bool:
    return self.check_update_access(g.authenticated_user)

  def check_update_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    elif self.entity_ref.group is not None:
      ug = self.entity_ref.group.get_member(user)
      if ug is None or ug.role == GroupRoles.readonly:
        return False
      else:
        return True
    else:
      return False
    
