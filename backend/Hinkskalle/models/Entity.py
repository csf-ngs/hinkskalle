from Hinkskalle import db
from marshmallow import fields, Schema
from datetime import datetime

class EntitySchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)
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
  quota = db.Column(db.Integer, default=0)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime)

  owner = db.relationship('User', back_populates='entities')

  collections_ref = db.relationship('Collection', back_populates='entity_ref', lazy='dynamic')

  def size(self):
    return self.collections_ref.count()

  def check_access(self, user):
    if user.is_admin:
      return True
    elif self.owner==user or self.name=='default':
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

