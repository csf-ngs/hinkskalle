from Hinkskalle import db
from datetime import datetime
from sqlalchemy.orm import validates

class Tag(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)

  image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
  image_ref = db.relationship('Image', back_populates='tags_ref')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime)

  owner = db.relationship('User', back_populates='tags')

  @validates('name')
  def convert_lower(self, key, value):
    return value.lower()


  __table_args__ = (db.UniqueConstraint('name', 'image_id', name='name_image_id_idx'),)