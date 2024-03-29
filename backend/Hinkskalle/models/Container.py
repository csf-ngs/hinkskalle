import typing
from flask import current_app, g
from Hinkskalle import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound # type: ignore
import enum

from Hinkskalle.models.Image import Image, UploadStates
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.User import GroupRoles, User

from marshmallow import fields, Schema, validates_schema, ValidationError
from ..util.name_check import validate_name
from ..util.schema import BaseSchema, LocalDateTime

class ContainerTypes(enum.Enum):
  singularity = 'singularity'
  docker = 'docker'
  generic = 'generic'
  mixed = 'mixed'


class ContainerSchema(BaseSchema):
  id = fields.String(dump_only=True, required=True)
  name = fields.String(required=True)
  description = fields.String(allow_none=True)
  fullDescription = fields.String(allow_none=True)
  private = fields.Boolean()
  readOnly = fields.Boolean()
  size = fields.Integer(dump_only=True)
  type = fields.String(dump_only=True)
  downloadCount = fields.Integer(dump_only=True)
  stars = fields.Integer(dump_only=True)
  customData = fields.String(allow_none=True)
  vcsUrl = fields.String(allow_none=True)
  usedQuota = fields.Integer(dump_only=True, attribute='used_quota')
  createdAt = LocalDateTime(dump_only=True)
  createdBy = fields.String(allow_none=True)
  updatedAt = LocalDateTime(dump_only=True, allow_none=True)
  deletedAt = LocalDateTime(dump_only=True, default=None)
  deleted = fields.Boolean(dump_only=True, default=False)

  # image ids, not used? keep to validate schema
  images = fields.List(fields.String(), dump_only=True, allow_none=True, attribute='image_names')

  collection = fields.String(required=True)
  collectionName = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)
  entityName = fields.String(dump_only=True)
  imageTags = fields.Dict(dump_only=True, allow_none=True)
  archTags = fields.Dict(dump_only=True, allow_none=True, attribute='archImageTags')

  canEdit = fields.Boolean(dump_only=True, default=False)

  @validates_schema
  def validate_name(self, data, **kwargs):
    errors = validate_name(data)
    if errors:
      raise ValidationError(errors)

class Container(db.Model): # type: ignore
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  description = db.Column(db.String())
  fullDescription = db.Column(db.String())
  private = db.Column(db.Boolean, default=False)
  readOnly = db.Column(db.Boolean, default=False)
  downloadCount = db.Column(db.Integer, default=0)
  latestDownload = db.Column(db.DateTime)
  #stars = db.Column(db.Integer, default=0)
  customData = db.Column(db.String())
  vcsUrl = db.Column(db.String())
  used_quota = db.Column(db.BigInteger(), default=0)

  collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  collection_ref = db.relationship('Collection', back_populates='containers_ref')
  images_ref = db.relationship('Image', back_populates='container_ref', lazy='dynamic', cascade='all, delete-orphan')
  tags_ref = db.relationship('Tag', back_populates='container_ref', cascade='all, delete-orphan')
  manifests_ref = db.relationship('Manifest', back_populates='container_ref', cascade='all, delete-orphan')

  owner = db.relationship('User', back_populates='containers')

  starred = db.relationship('User', secondary='user_stars', back_populates='starred')
  starred_sth = db.relationship('User', viewonly=True, secondary='user_stars', lazy='dynamic')

  @validates('name')
  def convert_lower(self, key, value: str) -> str:
    return value.lower()

  @property
  def stars(self) -> int:
    return self.starred_sth.count()

  __table_args__ = (db.UniqueConstraint('name', 'collection_id', name='name_collection_id_idx'),)

  @property
  def type(self) -> str:
    media_types = db.session.query(Image.media_type, func.count(Image.media_type)).filter(Image.container_id==self.id, Image.hide==False).group_by(Image.media_type).all()
    if len(media_types) == 1:
      if media_types[0][0] == Image.singularity_media_type:
        return ContainerTypes.singularity.name
      elif media_types[0][0].startswith('application/vnd.docker.image.rootfs.diff'):
        return ContainerTypes.docker.name
      else:
        return ContainerTypes.generic.name
    return ContainerTypes.mixed.name

  @property
  def size(self) -> int:
    if not self.id:
      return 0
    return self.images_ref.filter(Image.hide==False, Image.uploadState==UploadStates.completed).count()
  
  @property
  def collection(self) -> int:
    return self.collection_ref.id
  @property
  def collectionName(self) -> str:
    return self.collection_ref.name
  
  @property
  def entity(self) -> int:
    return self.collection_ref.entity_ref.id
  @property
  def entityName(self) -> str:
    return self.collection_ref.entity_ref.name

  def get_tag(self, tag: str, arch: typing.Optional[str]=None) -> Tag:
    cur_tags = Tag.query.filter(Tag.name == tag, Tag.container_id == self.id)
    if not arch or arch == current_app.config['DEFAULT_ARCH']:
      cur_tags = cur_tags.filter(or_(Tag.arch == current_app.config['DEFAULT_ARCH'], Tag.arch == None))
    else:
      cur_tags = cur_tags.filter(Tag.arch == arch)

    if cur_tags.count() > 1:
      raise Exception(f"Multiple tags {tag} found on container {self.id}")

    return cur_tags.first()


  def tag_image(self, tag: str, image_id: int, arch: typing.Optional[str]=None) -> Tag:
    errors = validate_name({ 'name': tag })
    if errors:
      raise ValidationError(errors)

    image = Image.query.get(image_id)
    if not image:
      raise NoResultFound()

    if not arch:
      arch = image.arch or current_app.config.get('DEFAULT_ARCH')
    image.arch=arch
    
    cur_tag = self.get_tag(tag, arch) 

    if cur_tag:
      cur_tag.image_ref=image
      cur_tag.updatedAt=datetime.now()
      db.session.commit()
    else:
      cur_tag = Tag(name=tag, container_ref=self, image_ref=image, arch=arch)
      db.session.add(cur_tag)
      db.session.commit()
    return cur_tag

  @property
  def imageTags(self) -> dict:
    tags = {}
    for tag in Tag.query.filter(Tag.container_ref==self, or_(Tag.arch==None, Tag.arch==current_app.config['DEFAULT_ARCH'])).all():
      tags[tag.name] = str(tag.image_id)
    return tags

  @property
  def archImageTags(self) -> dict:
    tags = {}
    for tag in self.tags_ref:
      arch = tag.arch or current_app.config.get('DEFAULT_ARCH')
      if not arch:
        continue
      tags[arch] = tags.get(arch, {})
      tags[arch][tag.name]=str(tag.image_id)
    return tags
  
  def check_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    else:
      return self.collection_ref.check_access(user)
  
  @property
  def canEdit(self) -> bool:
    return self.check_update_access(g.authenticated_user)

  def check_update_access(self, user: User) -> bool:
    if user.is_admin:
      return True
    elif self.owner == user:
      return True
    elif self.collection_ref.entity_ref.group:
      ug = self.collection_ref.entity_ref.group.get_member(user)
      if ug is None or ug.role == GroupRoles.readonly:
        return False
      else:
        return True
    else:
      return False