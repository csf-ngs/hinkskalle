from Hinkskalle import db
from marshmallow import fields, Schema
from datetime import datetime

class EntitySchema(Schema):
  id = fields.Integer(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  size = fields.Integer(dump_only=True)
  quota = fields.Integer(dump_only=True)
  defaultPrivate = fields.Boolean()
  customData = fields.String(allow_none=True)

  collections = fields.String(dump_only=True, many=True)


class Entity(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), unique=True, nullable=False)
  description = db.Column(db.String())
  customData = db.Column(db.String())

  defaultPrivate = db.Column(db.Boolean, default=False)
  quoate = db.Column(db.Integer, default=0)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deletedAt = db.Column(db.DateTime)
  deleted = db.Column(db.Boolean, default=False, nullable=False)

  collections = db.relationship('Collection', backref='entity_ref', lazy=True)

  def size(self):
    return len(self.collections) 

  def check_access(self, fsk_user):
    if fsk_user.is_admin:
      return True
    elif self.createdBy==fsk_user.username or self.name=='default':
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

