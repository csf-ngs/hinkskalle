from typing import Union
from Hinkskalle import db
from flask import current_app
from datetime import datetime
import json
import hashlib
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields

class ManifestLayerSchema(Schema):
  """https://github.com/opencontainers/image-spec/blob/v1.0.1/descriptor.md"""
  mediaType = fields.String()
  digest = fields.String()
  size = fields.Integer()
  urls = fields.Nested(fields.String(), many=True)
  annotations = fields.Dict()

class ManifestConfigSchema(Schema):
  """https://github.com/opencontainers/image-spec/blob/v1.0.1/config.md"""
  mediaType = fields.String()
  created = fields.String()
  author = fields.String()
  architecture = fields.String() # required 
  os = fields.String() # required
  config = fields.Dict() # could be specified 
  rootfs = fields.Dict()
  history = fields.Nested(fields.Dict(), many=True)

class ManifestSchema(Schema):
  schemaVersion = fields.String(required=True)
  config = fields.Nested(ManifestConfigSchema())
  layers = fields.Nested(ManifestLayerSchema(), many=True)
  annotations = fields.Dict()

class Manifest(db.Model):
  id = db.Column(db.Integer, primary_key=True)

  tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False, unique=True)
  tag_ref = db.relationship('Tag', back_populates='manifest_ref')

  hash = db.Column(db.String(), nullable=False, unique=True)
  _content = db.Column('content', db.String(), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  @hybrid_property
  def content(self) -> str:
    return self._content
  
  @content.setter
  def content(self, upd: Union[str, dict]):
    if type(upd) is str:
      self._content = upd
    else:
      # XXX check schema?
      self._content = json.dumps(upd)
    
    digest = hashlib.sha256()
    digest.update(self._content.encode('utf8'))
    self.hash = digest.hexdigest()

  @property
  def content_json(self) -> dict:
    return json.loads(self._content)