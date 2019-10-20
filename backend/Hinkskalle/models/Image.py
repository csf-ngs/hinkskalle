from mongoengine import Document, StringField, IntField, BooleanField, ReferenceField, DateTimeField
from marshmallow import Schema, fields
from datetime import datetime

from Hinkskalle.models import Tag

class ImageSchema(Schema):
  id = fields.String(required=True)
  description = fields.String(allow_none=True)
  hash = fields.String(allow_none=True)
  blob = fields.String()
  size = fields.Int()
  uploaded = fields.Boolean(dump_only=True)
  createdAt = fields.DateTime(dump_unly=True)
  updatedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deletedAt = fields.DateTime(dump_unly=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)

  container = fields.String(dump_only=True)
  containerName = fields.String(dump_only=True)
  collection = fields.String(dump_only=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  tags = fields.List(fields.String(), dump_only=True)

class Image(Document):
  id = StringField(required=True, primary_key=True)
  description = StringField()
  hash = StringField()
  blob = StringField()
  size = IntField(min_value=0)
  uploaded = BooleanField()
  container_ref = ReferenceField('Container')

  createdAt = DateTimeField(default=datetime.utcnow)
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  def container(self):
    return self.container_ref.id
  def containerName(self):
    return self.container_ref.name

  def collection(self):
    return self.container_ref.collection_ref.id
  def collectionName(self):
    return self.container_ref.collection_ref.name

  def entity(self):
    return self.container_ref.collection_ref.entity_ref.id
  def entityName(self):
    return self.container_ref.collection_ref.entity_ref.name
  
  def tags(self):
    return [ tag.name for tag in Tag.objects(image_ref=self) ]
   
