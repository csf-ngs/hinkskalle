import typing
from Hinkskalle import db
from marshmallow import fields, validates_schema, ValidationError
from datetime import datetime
from sqlalchemy.orm import validates
from flask import g
from Hinkskalle.models.Image import UploadStates
from Hinkskalle.util.name_check import validate_name
from Hinkskalle.models.User import GroupRoles, User
from ..util.schema import LocalDateTime, BaseSchema


class EntitySchema(BaseSchema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    createdAt = LocalDateTime(dump_only=True)
    createdBy = fields.String(allow_none=True)
    updatedAt = LocalDateTime(dump_only=True, allow_none=True)
    deletedAt = LocalDateTime(dump_only=True, default=None)
    deleted = fields.Boolean(dump_only=True, default=False)
    size = fields.Integer(dump_only=True)
    quota = fields.Integer(dump_only=True)
    usedQuota = fields.Integer(dump_only=True, attribute="used_quota")
    defaultPrivate = fields.Boolean()
    customData = fields.String(allow_none=True)

    isGroup = fields.Boolean(dump_only=True, attribute="is_group")
    groupRef = fields.String(dump_only=True, allow_none=True, attribute="group_ref")

    collections = fields.List(fields.String(), allow_none=True, dump_only=True)

    canEdit = fields.Boolean(default=False, dump_only=True)

    @validates_schema
    def validate_name(self, data, **kwargs):
        errors = validate_name(data)
        if errors:
            raise ValidationError(errors)


class Entity(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String())
    customData = db.Column(db.String())

    defaultPrivate = db.Column(db.Boolean, default=False)
    used_quota = db.Column(db.BigInteger, default=0)

    createdAt = db.Column(db.DateTime, default=datetime.now)
    createdBy = db.Column(db.String(), db.ForeignKey("user.username"))
    updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), unique=True)

    owner = db.relationship("User", back_populates="entities")
    group = db.relationship("Group", back_populates="entity")

    collections_ref = db.relationship("Collection", back_populates="entity_ref", lazy="dynamic")

    @validates("name")
    def convert_lower(self, key, value: str) -> str:
        return value.lower()

    @property
    def size(self) -> int:
        return self.collections_ref.count()

    @property
    def is_group(self) -> bool:
        return self.group_id is not None

    @property
    def group_ref(self) -> typing.Optional[str]:
        return self.group.name if self.group else None

    @property
    def quota(self) -> int:
        if self.group:
            return self.group.quota
        elif self.owner:
            return self.owner.quota
        else:
            return 0

    def calculate_used(self) -> int:
        entity_size = 0
        counted = {}
        # naive implementation. could be faster if we let
        # the db do the heavy lifiting. let's see.
        for collection in self.collections_ref:
            collection_size = 0
            collection_counted = {}
            for container in collection.containers_ref:
                container_size = 0
                container_counted = {}
                for img in container.images_ref:
                    if img.uploadState != UploadStates.completed or img.size is None:
                        continue
                    if not counted.get(img.location):
                        counted[img.location] = True
                        entity_size += img.size
                    if not container_counted.get(img.location):
                        container_counted[img.location] = True
                        container_size += img.size
                    if not collection_counted.get(img.location):
                        collection_counted[img.location] = True
                        collection_size += img.size
                container.used_quota = container_size
            collection.used_quota = collection_size
        self.used_quota = entity_size
        return entity_size

    def check_access(self, user: User) -> bool:
        if user.is_admin:
            return True
        elif self.owner == user:
            return True
        elif self.name == "default":
            return True
        elif self.group is not None:
            ug = self.group.get_member(user)
            return ug is not None
        else:
            return False

    @property
    def canEdit(self) -> bool:
        return self.check_update_access(g.authenticated_user)

    def check_update_access(self, user: User) -> bool:
        if user.is_admin:
            return True
        elif self.owner == user:
            return True
        elif self.group is not None:
            ug = self.group.get_member(user)
            if ug is None or ug.role == GroupRoles.readonly:
                return False
            else:
                return True
        else:
            return False
