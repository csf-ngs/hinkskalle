from mongoengine import Document, StringField, ListField, ReferenceField, BooleanField

from Hinkskalle.models import Collection, Image, Tag

from marshmallow import fields, Schema

class ContainerSchema(Schema):
  id = fields.String(required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  private = fields.Boolean()
  readOnly = fields.Boolean()
  deleted = fields.Boolean(dump_only=True)
  collection = fields.String(dump_only=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  imageTags = fields.Dict(dump_only=True)

class Container(Document):
  id = StringField(required=True, primary_key=True)
  name = StringField(required=True)
  description = StringField()
  private = BooleanField(default=False)
  readOnly = BooleanField(default=False)
  collection_ref = ReferenceField(Collection)

  deleted = BooleanField(required=True, default=False)
  
  def collection(self):
    return self.collection_ref.id
  def collectionName(self):
    return self.collection_ref.name
  
  def entity(self):
    return self.collection_ref.entity_ref.id
  def entityName(self):
    return self.collection_ref.entity_ref.name

  def images(self):
    return Image.objects(container_ref=self)
  
  def tag_image(self, tag, image_id):
    image = Image.objects.get(id=image_id)
    cur_tag = Tag.objects(name=tag, image_ref__in=self.images()).first()
    if cur_tag:
      cur_tag.image_ref=image
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
        tags[tag]=image.id
    return tags