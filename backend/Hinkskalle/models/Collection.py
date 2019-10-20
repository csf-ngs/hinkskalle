from mongoengine import Document, StringField, ReferenceField, BooleanField, DateTimeField
from marshmallow import Schema, fields
from datetime import datetime

from Hinkskalle.models import Entity

class CollectionSchema(Schema):
  id = fields.String(required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_unly=True)
  updatedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deletedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)


class Collection(Document):
  id = StringField(required=True, primary_key=True)
  name = StringField(required=True)
  description = StringField()
  entity_ref = ReferenceField(Entity)

  createdAt = DateTimeField(default=datetime.utcnow)
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  def entity(self):
    return self.entity_ref.id
  def entityName(self):
    return self.entity_ref.name