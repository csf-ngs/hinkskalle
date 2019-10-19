from mongoengine import Document, StringField, ReferenceField, BooleanField
from marshmallow import Schema, fields

from Hinkskalle.models import Entity

class CollectionSchema(Schema):
  id = fields.String(required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)


class Collection(Document):
  id = StringField(required=True, primary_key=True)
  name = StringField(required=True)
  description = StringField()
  entity_ref = ReferenceField(Entity)

  deleted = BooleanField(required=True, default=False)

  def entity(self):
    return self.entity_ref.id
  def entityName(self):
    return self.entity_ref.name