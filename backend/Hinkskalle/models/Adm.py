from Hinkskalle import db
from datetime import datetime
import enum

from marshmallow import fields, Schema

class AdmSchema(Schema):
  key = fields.String(required=True)
  val = fields.Dict(required=True, default={})

class AdmKeys(enum.Enum):
  ldap_sync_results = 'ldap_sync_results'

class Adm(db.Model):
  key = db.Column(db.Enum(AdmKeys), primary_key=True)
  val = db.Column(db.JSON(), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String())
  updatedAt = db.Column(db.DateTime)
  updatedBy = db.Column(db.String())