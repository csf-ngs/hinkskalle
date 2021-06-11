from typing import Union

from sqlalchemy.orm.exc import NoResultFound
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

  container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)
  container_ref = db.relationship('Container', back_populates='manifests_ref')

  tags = db.relationship('Tag', back_populates='manifest_ref')

  hash = db.Column(db.String(), nullable=False)
  _content = db.Column('content', db.String(), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  __table_args__ = (db.UniqueConstraint('hash', 'container_id', name='manifest_hash_container_idx'),)

  @property
  def stale(self) -> bool:
    from Hinkskalle.models.Image import Image
    # singularity images can also be pushed via library protocol.
    # if any of those has a hash that is different from the one in our layer
    # we have to update the manifest.
    # all other layer types can only be pushed via the OCI API and should not
    # be out of date.
    content = self.content_json
    if not 'layers' in content:
      return False
    for layer in content['layers']:
      if layer.get('mediaType') != Image.singularity_media_type:
        continue
      # check if referenced image does not exist anymore
      try:
        ref = Image.query.filter(Image.container_id==self.container_id, Image.hash==layer.get('digest').replace('sha256:', 'sha256.')).one()
      except NoResultFound:
        return True
      # check if tags point to same image
      for tag in self.tags:
        if tag.image_ref.hash.replace('sha256.', 'sha256:') != layer.get('digest'):
          return True
    return False
      


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