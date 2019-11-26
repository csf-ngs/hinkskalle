from mongoengine import Document, StringField, ReferenceField, BooleanField, DateTimeField
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
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)
  size = fields.Integer(dump_only=True)
  private = fields.Boolean()
  customData = fields.String(allow_none=True)

  entity = fields.String(required=True)
  entityName = fields.String(dump_only=True)

  containers = fields.String(dump_only=True, many=True)


class Collection(Document):
  name = StringField(required=True, unique_with='entity_ref')
  description = StringField()
  customData = StringField()
  private = BooleanField(default=False)

  entity_ref = ReferenceField(Entity, required=True)

  createdAt = DateTimeField(default=datetime.utcnow)
  createdBy = StringField()
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  def size(self):
    from Hinkskalle.models import Container
    return Container.objects(collection_ref=self).count() if not self._created else 0

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
    
