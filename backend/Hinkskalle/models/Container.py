from Hinkskalle import db
from datetime import datetime
from sqlalchemy.orm import validates

from Hinkskalle.models import Collection, Image, Tag

from marshmallow import fields, Schema, validates_schema, ValidationError
from Hinkskalle.util.name_check import validate_name

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
  createdBy = fields.String(allow_none=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

  # image ids, not used? keep to validate schema
  images = fields.String(dump_only=True, many=True, attribute='image_names')

  collection = fields.String(required=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  imageTags = fields.Dict(dump_only=True, allow_none=True)
  archTags = fields.Dict(dump_only=True, allow_none=True)

  @validates_schema
  def validate_name(self, data, **kwargs):
    errors = validate_name(data)
    if errors:
      raise ValidationError(errors)

class Container(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  fullDescription = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)
  readOnly = db.Column(db.Boolean, default=False)
  downloadCount = db.Column(db.Integer, default=0)
  #stars = db.Column(db.Integer, default=0)
  customData = db.Column(db.String())
  vcsUrl = db.Column(db.String())

  collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime)

  collection_ref = db.relationship('Collection', back_populates='containers_ref')
  images_ref = db.relationship('Image', back_populates='container_ref', lazy='dynamic')
  owner = db.relationship('User', back_populates='containers')

  starred = db.relationship('User', secondary='user_stars', back_populates='starred')
  starred_sth = db.relationship('User', viewonly=True, secondary='user_stars', lazy='dynamic')

  @validates('name')
  def convert_lower(self, key, value):
    return value.lower()

  @property
  def stars(self):
    return self.starred_sth.count()

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
    errors = validate_name({ 'name': tag })
    if errors:
      raise ValidationError(errors)

    image = Image.query.get(image_id)
    cur_tag = Tag.query.filter(Tag.name == tag, Tag.image_id.in_([ i.id for i in self.images_ref ])).first()
    if cur_tag:
      cur_tag.image_ref=image
      cur_tag.updatedAt=datetime.now()
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
    # XXX
    return {}
  
  def check_access(self, user):
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return self.collection_ref.check_access(user)
  
  def check_update_access(self, user):
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return False