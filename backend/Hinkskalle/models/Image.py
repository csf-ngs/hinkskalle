from Hinkskalle.models.Manifest import Manifest
from typing import List

from sqlalchemy.ext.hybrid import hybrid_property
from Hinkskalle import db
from Hinkskalle.models.User import User
from flask import current_app
from marshmallow import Schema, fields
from datetime import datetime, timedelta
import json
import re
import uuid
import enum

import os.path
import subprocess


class ImageSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  description = fields.String(allow_none=True)
  hash = fields.String(allow_none=True)
  blob = fields.String(allow_none=True)
  size = fields.Int(allow_none=True, dump_only=True)
  uploaded = fields.Boolean()
  customData = fields.String(allow_none=True)
  arch = fields.String(allow_none=True)
  signed = fields.Boolean(allow_none=True, dump_only=True)
  signatureVerified = fields.Boolean(allow_none=True, dump_only=True)
  encrypted = fields.Boolean(allow_none=True)
  type = fields.String(dump_only=True)

  containerStars = fields.Integer(dump_only=True)
  containerDownloads = fields.Integer(dump_only=True)
  downloadCount = fields.Integer(dump_only=True)

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
  expiresAt = fields.DateTime(allow_none=True)

  deletedAt = fields.DateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

  container = fields.String(required=True)
  containerName = fields.String(dump_only=True)
  collection = fields.String(dump_only=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  tags = fields.List(fields.String(), dump_only=True)
  fingerprints = fields.List(fields.String(), dump_only=True)

def generate_uuid() -> str:
  return str(uuid.uuid4())
def upload_expiration() -> datetime:
  return datetime.now() + timedelta(minutes=5)

class UploadStates(enum.Enum):
  initialized = 'initialized'
  uploading = 'uploading'
  uploaded = 'uploaded'
  failed = 'failed'
  completed = 'completed'

class UploadTypes(enum.Enum):
  single = 'single'
  # OCI push doesn't let us differentiate between single and multipart uploads
  # on init, it seems.
  undetermined = 'undetermined'
  multipart = 'multipart'
  multipart_chunk = 'multipart_chunk'

class ImageUploadUrl(db.Model):
  id = db.Column(db.String(), primary_key=True, default=generate_uuid, unique=True)
  expiresAt = db.Column(db.DateTime, default=upload_expiration)
  path = db.Column(db.String(), nullable=False)
  size = db.Column(db.BigInteger())
  md5sum = db.Column(db.String())
  sha256sum = db.Column(db.String())
  state = db.Column(db.Enum(UploadStates, name="upload_state_types"))
  type = db.Column(db.Enum(UploadTypes, name="upload_types"))
  partNumber = db.Column(db.Integer)
  totalParts = db.Column(db.Integer)
  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  owner = db.relationship('User')

  parent_id = db.Column(db.String, db.ForeignKey('image_upload_url.id', ondelete='CASCADE'), nullable=True)
  parent_ref = db.relationship('ImageUploadUrl', back_populates='parts_ref', remote_side=[id])

  image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='CASCADE'), nullable=False)
  image_ref = db.relationship('Image', back_populates='uploads_ref')

  parts_ref = db.relationship('ImageUploadUrl', back_populates='parent_ref', lazy='dynamic', cascade="all, delete-orphan")

  def check_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return False

class ImageTypes(enum.Enum):
  singularity = 'singularity'
  docker = 'docker'
  oci = 'oci'
  other = 'other'

class Image(db.Model):
  valid_media_types = {
    'application/vnd.docker.image.rootfs.diff.tar.gzip': True,
    'application/vnd.oci.image.layer.v1.tar+gzip': True,
    'application/vnd.oci.image.layer.v1.tar': True,
    'application/vnd.sylabs.sif.layer.v1.sif': True,
  }
  singularity_media_type = 'application/vnd.sylabs.sif.layer.v1.sif'

  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String())

  hash = db.Column(db.String())
  blob = db.Column(db.String())
  size = db.Column(db.BigInteger())
  uploaded = db.Column(db.Boolean, default=False)
  customData = db.Column(db.String())
  downloadCount = db.Column(db.Integer, default=0)
  latestDownload = db.Column(db.DateTime)
  arch = db.Column(db.String())
  signed = db.Column(db.Boolean, default=False)
  signatureVerified = db.Column(db.Boolean, default=False)
  encrypted = db.Column(db.Boolean, default=False)
  sigdata = db.Column(db.JSON())

  _media_type = db.Column('media_type', db.String(), default=singularity_media_type)
  hide = db.Column(db.Boolean(), default=False)

  container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)
  expiresAt = db.Column(db.DateTime)

  owner = db.relationship('User', back_populates='images')

  location = db.Column(db.String())

  container_ref = db.relationship('Container', back_populates='images_ref')
  tags_ref = db.relationship('Tag', back_populates='image_ref', lazy='dynamic', cascade="all, delete-orphan")
  uploads_ref = db.relationship('ImageUploadUrl', back_populates='image_ref', lazy='dynamic', cascade="all, delete", passive_deletes=True)

  __table_args__ = (db.UniqueConstraint('hash', 'container_id', name='hash_container_id_idx'),)

  def generate_manifest(self) -> Manifest:
    if not self.media_type == Image.singularity_media_type:
      raise Exception(f"Refusing to create manifest for non-singularity media type {self.media_type}")
    data = {
      'schemaVersion': 2,
      'config': {
        'mediaType': 'application/vnd.sylabs.sif.config.v1',
      },
      'layers': [{
        # see https://github.com/opencontainers/image-spec/blob/master/descriptor.md
        'mediaType': self.media_type,
        'digest': self.hash.replace('sha256.', 'sha256:'),
        'size': self.size,
        # singularity does not pull without a name
        # could provide more annotations!
        'annotations': {
          # singularity oras pull needs this!
          'org.opencontainers.image.title': self.container_ref.name,
        }
      }]
    }
    with db.session.no_autoflush:
      manifest = Manifest(content=data)
      existing = Manifest.query.filter(Manifest.hash == manifest.hash).first()
      if existing:
        manifest = existing
    
    db.session.add(manifest)
    manifest.container_ref=self.container_ref
    db.session.commit()
    
    return manifest

  @hybrid_property
  def media_type(self) -> str:
    return self._media_type
  
  @media_type.setter
  def media_type(self, upd: str):
    if upd is None or self.valid_media_types.get(upd):
      self.hide = False
    elif upd is not None:
      self.hide = True
    self._media_type = upd

  @property
  def type(self) -> str:
    if self.media_type == 'application/vnd.docker.image.rootfs.diff.tar.gzip':
      return ImageTypes.docker.name
    elif self.media_type == 'application/vnd.oci.image.layer.v1.tar+gzip' or self.media_type == 'application/vnd.oci.image.layer.v1.tar':
      return ImageTypes.oci.name
    elif self.media_type == self.singularity_media_type:
      return ImageTypes.singularity.name
    else:
      return ImageTypes.other.name


  @property
  def fingerprints(self) -> set:
    if self.sigdata is None or self.sigdata.get('SignerKeys', None) is None:
      return set()
    
    ret = []
    for key in self.sigdata.get('SignerKeys'):
      ret.append(key['Signer']['Fingerprint'])
    return set(ret)

  @property
  def tags(self) -> List[str]:
    return [ tag.name for tag in self.tags_ref ]

  @property
  def container(self) -> int:
    return self.container_ref.id
  @property
  def containerName(self) -> str:
    return self.container_ref.name
  @property
  def containerStars(self) -> int:
    return self.container_ref.stars
  @property
  def containerDownloads(self) -> int:
    return self.container_ref.downloadCount

  @property
  def collection(self) -> int:
    return self.container_ref.collection_ref.id
  @property
  def collectionName(self) -> str:
    return self.container_ref.collection_ref.name

  @property
  def entity(self) -> int:
    return self.container_ref.collection_ref.entity_ref.id
  @property
  def entityName(self) -> str:
    return self.container_ref.collection_ref.entity_ref.name
  
  def make_prettyname(self, tag: str) -> str:
    fn = os.path.join(self.entityName, self.collectionName, f"{self.containerName}_{tag}")
    if self.media_type == self.singularity_media_type:
      fn+='.sif'
    return fn

  def make_filename(self) -> str:
    fn=self.hash
    if self.media_type == self.singularity_media_type:
      fn+=".sif"
    return fn
  
  def _check_file(self) -> None:
    if not self.uploaded or not self.location:
      raise Exception("Image is not uploaded yet")
    if not os.path.exists(self.location):
      raise Exception(f"Image file at {self.location} does not exist")
    
  
  # currently using siftool to extract definition file only
  # "singularity inspect" needs to actually spin up the container
  # and works only when we're launched in privileged mode (or bareback)
  # tags are stored in the actual container file system (squashfs) -
  # metadata partitions are a thing of the future!
  def inspect(self) -> str:
    self._check_file()
    if self.media_type != self.singularity_media_type:
      raise Exception(f"not a singularity image: {self.media_type}")
    inspect = subprocess.run(["singularity", "sif", "dump", "1", self.location], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not inspect.returncode == 0:
      raise Exception(f"{inspect.args} failed: {inspect.stderr}")

    return inspect.stdout.decode('utf-8')
  
  def check_signature(self) -> dict:
    self.sigdata = self._get_signature();
    if self.sigdata.get('Signatures', 0) >= 1:
      self.signed = True
      self.signatureVerified = self.sigdata.get('Passed', False)
    else:
      self.signed = False

    return self.sigdata

  def _get_signature(self) -> dict:
    self._check_file()
    if self.media_type != self.singularity_media_type:
      return { 'Passed': False, 'Reason': 'NotApplicable' }
    proc = subprocess.run(["singularity", "verify", "--url", current_app.config['KEYSERVER_URL'], "--json", self.location], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sigdata = json.loads(proc.stdout)
    if not proc.returncode == 0:
      stderr = proc.stderr.decode('utf-8')
      sigdata["Passed"]=False
      ## could be unsigned/unknown signer
      if re.search(r"signature not found", stderr):
        sigdata["Reason"]='Unsigned'
      elif re.search(r"signature made by unknown entity", stderr):
        sigdata["Reason"]='Unknown'
      else:
        raise Exception(stderr)
    else:
      sigdata["Passed"]=True
    return sigdata
  
    
  def check_access(self, user) -> bool:
    if not self.container_ref.private:
      return True
    
    if not user:
      return False
    
    return self.container_ref.check_access(user)
  
  def check_update_access(self, user) -> bool:
    return self.container_ref.check_update_access(user)
   
