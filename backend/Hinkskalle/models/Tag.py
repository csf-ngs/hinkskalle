from Hinkskalle import db
from datetime import datetime

class Tag(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)

  image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.utcnow)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  deletedAt = db.Column(db.DateTime)

  __table_args__ = (db.UniqueConstraint('name', 'image_id', name='name_image_id_idx'),)