from mongoengine import Document, StringField, BooleanField
from marshmallow import fields, Schema

class EntitySchema(Schema):
  id = fields.String(required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  deleted = fields.Boolean(dump_only=True)


class Entity(Document):
  id = StringField(required=True, primary_key=True)
  name = StringField(required=True)
  description = StringField()

  deleted = BooleanField(required=True, default=False)