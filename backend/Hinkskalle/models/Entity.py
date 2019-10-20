from mongoengine import Document, StringField, BooleanField, DateTimeField
from marshmallow import fields, Schema
from datetime import datetime

class EntitySchema(Schema):
  id = fields.String(required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_unly=True)
  updatedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deletedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)


class Entity(Document):
  id = StringField(required=True, primary_key=True)
  name = StringField(required=True)
  description = StringField()

  createdAt = DateTimeField(default=datetime.utcnow)
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)