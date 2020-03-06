from Hinkskalle import db
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
  vcsUrl = fields.String(allow_none=True)
  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True, allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, allow_none=True)
  deleted = fields.Boolean(dump_only=True)

  # image ids, not used? keep to validate schema
  images = fields.String(dump_only=True, many=True, attribute='image_names')

  collection = fields.String(required=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  imageTags = fields.Dict(dump_only=True, allow_none=True)
  archTags = fields.Dict(dump_only=True, allow_none=True)

class Container(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  fullDescription = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)
  readOnly = db.Column(db.Boolean, default=False)
  downloadCount = db.Column(db.Integer, default=0)
  stars = db.Column(db.Integer, default=0)
  customData = db.Column(db.String())
  vcsUrl = db.Column(db.String())

  collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deletedAt = db.Column(db.DateTime)
  deleted = db.Column(db.Boolean, default=False, nullable=False)

  images_ref = db.relationship('Image', backref='container_ref', lazy='dynamic')

  __table_args__ = (db.UniqueConstraint('name', 'collection_id', name='name_collection_id_idx'),)

  def size(self):
    return self.images_ref.count()
  
  def collection(self):
    return self.collection_ref.id
  def collectionName(self):
    return self.collection_ref.name
  
  def entity(self):
    return self.collection_ref.entity_ref.id
  def entityName(self):
    return self.collection_ref.entity_ref.name

  def tag_image(self, tag, image_id):
    image = Image.query.get(image_id)
    cur_tag = Tag.query.filter(Tag.name == tag, Tag.image_id.in_([ i.id for i in self.images_ref ])).first()
    if cur_tag:
      cur_tag.image_ref=image
      cur_tag.updatedAt=datetime.utcnow()
      db.session.commit()
    else:
      cur_tag = Tag(name=tag, image_ref=image)
      db.session.add(cur_tag)
      db.session.commit()
    return cur_tag

  def imageTags(self):
    tags = {}
    for image in self.images_ref:
      for tag in image.tags():
        if tag in tags:
          raise Exception(f"Tag {tag} for image {image.id} is already set on {tags[tag]}")
        tags[tag]=str(image.id)
    return tags

  def archTags(self):
    return {}
  
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