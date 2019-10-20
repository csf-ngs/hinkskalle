from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField
from marshmallow import fields, Schema
from datetime import datetime

class EntitySchema(Schema):
  id = fields.String(required=True, dump_only=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_unly=True)
  createdBy = fields.String(dump_unly=True, allow_none=True)
  updatedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deletedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  size = fields.Integer(dump_only=True)
  quota = fields.Integer(dump_only=True)
  defaultPrivate = fields.Boolean()
  customData = fields.String()

  collections = fields.String(dump_only=True, many=True)


class Entity(Document):
  name = StringField(required=True, unique=True)
  description = StringField()
  customData = StringField()
  defaultPrivate = BooleanField(default=False)
  quota = IntField(default=0)

  createdAt = DateTimeField(default=datetime.utcnow)
  createdBy = StringField()
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  def size(self):
    return 0