from Hinkskalle import db
from datetime import datetime
import enum

from marshmallow import fields, Schema, validate, pre_dump

class AdmKeys(enum.Enum):
  ldap_sync_results = 'ldap_sync_results'
  check_quotas = 'check_quotas'
  expire_images = 'expire_images'

class AdmSchema(Schema):
  key = fields.String(required=True, dump_only=True, validate=validate.OneOf([k.name for k in AdmKeys ]))
  val = fields.Dict(required=True, default={})

  @pre_dump
  def unwrap_key(self, data, **kwargs):
    data.key=data.key.name
    return data

class Adm(db.Model):
  key = db.Column(db.Enum(AdmKeys, name="adm_key_types"), primary_key=True)
  val = db.Column(db.JSON(), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)
  updatedBy = db.Column(db.String())