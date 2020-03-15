from Hinkskalle import db
from marshmallow import Schema, fields
from datetime import datetime

from Hinkskalle.models import Entity

class CollectionSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
  size = fields.Integer(dump_only=True)
  private = fields.Boolean()
  customData = fields.String(allow_none=True)

  entity = fields.String(required=True)
  entityName = fields.String(dump_only=True)

  containers = fields.String(dump_only=True, many=True)


class Collection(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  customData = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)

  entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime)

  entity_ref = db.relationship('Entity', back_populates='collections_ref')
  containers_ref = db.relationship('Container', back_populates='collection_ref', lazy='dynamic')
  owner = db.relationship('User', back_populates='collections')

  __table_args__ = (db.UniqueConstraint('name', 'entity_id', name='name_entity_id_idx'),)

  def size(self):
    return self.containers_ref.count()

  def entity(self):
    return self.entity_ref.id
  def entityName(self):
    return self.entity_ref.name
  
  def check_access(self, user):
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return False
  
  def check_update_access(self, user):
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return False
    
