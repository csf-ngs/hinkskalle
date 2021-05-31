from typing import Union
from Hinkskalle import db
from flask import current_app
from datetime import datetime
import json
import hashlib
from sqlalchemy.ext.hybrid import hybrid_property


class Manifest(db.Model):
  id = db.Column(db.Integer, primary_key=True)

  hash = db.Column(db.String(), nullable=False, unique=True)
  _content = db.Column('content', db.String(), nullable=False)

  image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
  image_ref = db.relationship('Image', back_populates='manifests_ref')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  @hybrid_property
  def content(self):
    return self._content
  
  @content.setter
  def content(self, upd: Union[str, dict]):
    if type(upd) is str:
      self._content = upd
    else:
      self._content = json.dumps(upd)
    
    digest = hashlib.sha256()
    digest.update(self._content.encode('utf8'))
    self.hash = digest.hexdigest()

