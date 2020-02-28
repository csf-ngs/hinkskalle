from Hinkskalle import db
from marshmallow import Schema, fields
from datetime import datetime

import os.path
from Hinkskalle.models import Tag

class ImageSchema(Schema):
  id = fields.Integer(required=True, dump_only=True)
  description = fields.String(allow_none=True)
  hash = fields.String()
  blob = fields.String(allow_none=True)
  size = fields.Int(allow_none=True, dump_only=True)
  uploaded = fields.Boolean()
  customData = fields.String(allow_none=True)

  containerStars = fields.Integer(dump_only=True)
  containerDownloads = fields.Integer(dump_only=True)
  downloadCount = fields.Integer(dump_only=True)

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

class Image(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String())

  hash = db.Column(db.String())
  blob = db.Column(db.String())
  size = db.Column(db.Integer)
  uploaded = db.Column(db.Boolean, default=False)
  customData = db.Column(db.String())
  downloadCount = db.Column(db.Integer, default=0)

  container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deletedAt = db.Column(db.DateTime)
  deleted = db.Column(db.Boolean, default=False, nullable=False)

  location = db.Column(db.String())

  tags_ref = db.relationship('Tag', backref='image_ref', lazy=True)

  __table_args__ = (db.UniqueConstraint('hash', 'container_id', name='hash_container_id_idx'),)

  def tags(self):
    return [ tag.name for tag in self.tags_ref ]

  def container(self):
    return self.container_ref.id
  def containerName(self):
    return self.container_ref.name
  def containerStars(self):
    return self.container_ref.stars
  def containerDownloads(self):
    return self.container_ref.downloadCount

  def collection(self):
    return self.container_ref.collection_ref.id
  def collectionName(self):
    return self.container_ref.collection_ref.name

  def entity(self):
    return self.container_ref.collection_ref.entity_ref.id
  def entityName(self):
    return self.container_ref.collection_ref.entity_ref.name
  
  def make_prettyname(self, tag):
    return os.path.join(self.entityName(), self.collectionName(), f"{self.containerName}_{tag}.sif")
  def make_filename(self):
    return f"{self.hash}.sif"
  
  def check_access(self, fsk_user):
    if not self.container_ref.private:
      return True
    
    if not fsk_user:
      return False
    
    return self.container_ref.check_access(fsk_user)
  
  def check_update_access(self, fsk_user):
    return self.container_ref.check_update_access(fsk_user)
   
