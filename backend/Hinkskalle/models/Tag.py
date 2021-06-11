from Hinkskalle.models.Image import Image
from Hinkskalle import db
from datetime import datetime
from sqlalchemy.orm import validates
from Hinkskalle.models.Manifest import Manifest

class Tag(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  arch = db.Column(db.String())

  container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)
  container_ref = db.relationship('Container', back_populates='tags_ref')

  image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
  image_ref = db.relationship('Image', back_populates='tags_ref')

  manifest_id = db.Column(db.Integer, db.ForeignKey('manifest.id'), nullable=True)
  manifest_ref: Manifest = db.relationship('Manifest', back_populates='tags')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  owner = db.relationship('User', back_populates='tags')
  __table_args__ = (db.UniqueConstraint('name', 'container_id', 'arch', name='tag_name_container_arch_idx'),)

  @validates('image_ref')
  def set_image(self, key, value):
    if value is None:
      self.container_ref=None
    else:
      self.arch=value.arch
      self.container_ref=value.container_ref
    return value

  @validates('name')
  def convert_lower(self, key, value):
    return value.lower()



