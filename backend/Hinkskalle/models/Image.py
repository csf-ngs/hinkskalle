from Hinkskalle import db
from flask import current_app
from marshmallow import Schema, fields
from datetime import datetime
import json
import re

import os.path
import subprocess
from Hinkskalle.models import Tag


class ImageSchema(Schema):
  id = fields.String(required=True, dump_only=True)
  description = fields.String(allow_none=True)
  hash = fields.String()
  blob = fields.String(allow_none=True)
  size = fields.Int(allow_none=True, dump_only=True)
  uploaded = fields.Boolean()
  customData = fields.String(allow_none=True)
  arch = fields.String(allow_none=True)
  signed = fields.Boolean(allow_none=True)
  signatureVerified = fields.Boolean(allow_none=True)
  encrypted = fields.Boolean(allow_none=True)

  containerStars = fields.Integer(dump_only=True)
  containerDownloads = fields.Integer(dump_only=True)
  downloadCount = fields.Integer(dump_only=True)

  createdAt = fields.DateTime(dump_only=True)
  createdBy = fields.String(dump_only=True)
  updatedAt = fields.DateTime(dump_only=True, allow_none=True)
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

class Image(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String())

  hash = db.Column(db.String())
  blob = db.Column(db.String())
  size = db.Column(db.Integer)
  uploaded = db.Column(db.Boolean, default=False)
  customData = db.Column(db.String())
  downloadCount = db.Column(db.Integer, default=0)
  arch = db.Column(db.String())
  signed = db.Column(db.Boolean, default=False)
  signatureVerified = db.Column(db.Boolean, default=False)
  encrypted = db.Column(db.Boolean, default=False)
  sigdata = db.Column(db.JSON())


  container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime)

  owner = db.relationship('User', back_populates='images')

  location = db.Column(db.String())

  container_ref = db.relationship('Container', back_populates='images_ref')
  tags_ref = db.relationship('Tag', back_populates='image_ref', lazy='dynamic', cascade="all, delete-orphan")

  __table_args__ = (db.UniqueConstraint('hash', 'container_id', name='hash_container_id_idx'),)

  @property
  def fingerprints(self):
    current_app.logger.debug(self.sigdata)
    if self.sigdata is None or self.sigdata.get('SignerKeys', None) is None:
      return []
    
    ret = []
    for key in self.sigdata.get('SignerKeys'):
      ret.append(key['Signer']['Fingerprint'])
    return set(ret)

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
  
  def _check_file(self):
    if not self.uploaded or not self.location:
      raise Exception("Image is not uploaded yet")
    if not os.path.exists(self.location):
      raise Exception(f"Image file at {self.location} does not exist")
    
  
  # currently using siftool to extract definition file only
  # "singularity inspect" needs to actually spin up the container
  # and works only when we're launched in privileged mode (or bareback)
  # tags are stored in the actual container file system (squashfs) -
  # metadata partitions are a thing of the future!
  def inspect(self):
    self._check_file()
    inspect = subprocess.run(["singularity", "sif", "dump", "1", self.location], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not inspect.returncode == 0:
      raise Exception(f"{inspect.args} failed: {inspect.stderr}")

    return inspect.stdout
  
  def check_signature(self):
    self.sigdata = self._get_signature();
    if self.sigdata.get('Signatures', None) == 1:
      self.signed = True
      self.signatureVerified = self.sigdata.get('Passed', False)
    else:
      self.signed = False

    return self.sigdata

  def _get_signature(self):
    self._check_file()
    proc = subprocess.run(["singularity", "verify", "--url", current_app.config.get('KEYSERVER_URL'), "--json", self.location], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    
  def check_access(self, user):
    if not self.container_ref.private:
      return True
    
    if not user:
      return False
    
    return self.container_ref.check_access(user)
  
  def check_update_access(self, user):
    return self.container_ref.check_update_access(user)
   
