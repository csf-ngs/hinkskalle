from mongoengine import Document, StringField, IntField, BooleanField, ReferenceField, DateTimeField
from marshmallow import Schema, fields
from datetime import datetime

import os.path
from Hinkskalle.models import Tag

class ImageSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  description = fields.String(allow_none=True)
  hash = fields.String()
  blob = fields.String(allow_none=True)
  size = fields.Int(allow_none=True)
  uploaded = fields.Boolean()
  customData = fields.String(allow_none=True)

  containerStars = fields.Integer(dump_only=True)
  containerDownloads = fields.Integer(dump_only=True)

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)

  container = fields.String(required=True)
  containerName = fields.String(dump_only=True)
  collection = fields.String(dump_only=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  tags = fields.List(fields.String(), dump_only=True)

class Image(Document):
  description = StringField()
  hash = StringField(unique_with='container_ref')
  blob = StringField()
  size = IntField(min_value=0)
  uploaded = BooleanField(default=False)
  customData = StringField()
  containerStars = IntField(default=0)
  containerDownload = IntField(default=0)

  container_ref = ReferenceField('Container')

  createdAt = DateTimeField(default=datetime.utcnow)
  createdBy = StringField()
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  location = StringField()

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
  
  def make_prettyname(self, tag):
    return os.path.join(self.entityName(), self.collectionName(), f"{self.containerName}_{tag}.sif")
  def make_filename(self):
    return f"{self.hash}.sif"
   
