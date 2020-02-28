from Hinkskalle import db
from marshmallow import Schema, fields
from datetime import datetime

from Hinkskalle.models import Entity

class CollectionSchema(Schema):
  id = fields.Integer(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  size = fields.Integer(dump_only=True)
  private = fields.Boolean()
  customData = fields.String(allow_none=True)

  entity = fields.Integer(required=True)
  entityName = fields.String(dump_only=True)

  containers = fields.String(dump_only=True, many=True)


class Collection(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  customData = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)

  entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deletedAt = db.Column(db.DateTime)
  deleted = db.Column(db.Boolean, default=False, nullable=False)

  containers = db.relationship('Container', backref='collection_ref', lazy=True)

  __table_args__ = (db.UniqueConstraint('name', 'entity_id', name='name_entity_id_idx'),)

  def size(self):
    return len(self.containers)

  def entity(self):
    return self.entity_ref.id
  def entityName(self):
    return self.entity_ref.name
  
  def check_access(self, fsk_user):
    if fsk_user.is_admin:
      return True
    elif self.createdBy == fsk_user.username:
      return True
    else:
      return False
  
  def check_update_access(self, fsk_user):
    if fsk_user.is_admin:
      return True
    elif self.createdBy == fsk_user.username:
      return True
    else:
      return False
    
