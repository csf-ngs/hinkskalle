from mongoengine import Document, StringField, ListField, ReferenceField, BooleanField, DateTimeField, IntField
from datetime import datetime

from Hinkskalle.models import Collection, Image, Tag

from marshmallow import fields, Schema

class ContainerSchema(Schema):
  id = fields.String(dump_only=True, required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  fullDescription = fields.String(allow_none=True)
  private = fields.Boolean()
  readOnly = fields.Boolean()
  size = fields.Integer(dump_only=True)
  downloadCount = fields.Integer(dump_only=True)
  stars = fields.Integer(dump_only=True)
  customData = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)

  collection = fields.String(required=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  imageTags = fields.Dict(dump_only=True, allow_none=True)
  archTags = fields.Dict(dump_only=True, allow_none=True)

  images = fields.String(dump_only=True, many=True, attribute='image_names')

class Container(Document):
  name = StringField(required=True, unique_with='collection_ref')
  description = StringField()
  fullDescription = StringField()
  private = BooleanField(default=False)
  readOnly = BooleanField(default=False)
  downloadCount = IntField(default=0)
  stars = IntField(default=0)
  customData = StringField()
  collection_ref = ReferenceField(Collection, required=True)

  createdAt = DateTimeField(default=datetime.utcnow)
  createdBy = StringField()
  updatedAt = DateTimeField()
  deletedAt = DateTimeField()
  deleted = BooleanField(required=True, default=False)

  def size(self):
    return 0
  
  def collection(self):
    return self.collection_ref.id
  def collectionName(self):
    return self.collection_ref.name
  
  def entity(self):
    return self.collection_ref.entity_ref.id
  def entityName(self):
    return self.collection_ref.entity_ref.name

  def image_names(self):
    imgs = list(self.images())
    if len(imgs) == 0:
      return None
    else:
      return [ img.name for img in imgs ]

  def images(self):
    return Image.objects(container_ref=self)
  
  def tag_image(self, tag, image_id):
    image = Image.objects.get(id=image_id)
    cur_tag = Tag.objects(name=tag, image_ref__in=self.images()).first()
    if cur_tag:
      cur_tag.image_ref=image
      cur_tag.updatedAt=datetime.utcnow()
      cur_tag.save()
    else:
      cur_tag = Tag(name=tag, image_ref=image)
      cur_tag.save()
    return cur_tag

  def imageTags(self):
    tags = {}
    for image in self.images():
      for tag in image.tags():
        if tag in tags:
          raise Exception(f"Tag {tag} for image {image.id} is already set on {tags[tag]}")
        tags[tag]=str(image.id)
    return tags

  def archTags(self):
    return {}