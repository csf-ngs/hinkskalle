from datetime import datetime, timedelta
from pprint import pprint
import typing

from sqlalchemy.exc import IntegrityError

from ..model_base import ModelBase
from .._util import _create_group, _create_user, _create_image, default_entity_name

from Hinkskalle.models import Group, GroupSchema, GroupRoles, UserGroup, Entity, UploadStates

from Hinkskalle import db


class TestGroup(ModelBase):
    def test_group(self):
        group = _create_group("Testhasenstall")
        db.session.add(group)
        db.session.commit()

        read_group = Group.query.filter_by(name="Testhasenstall").first()
        self.assertEqual(read_group.id, group.id)
        self.assertTrue(abs(read_group.createdAt - datetime.now()) < timedelta(seconds=2))

    def test_entity(self):
        group = _create_group("Testhasentall")

        entity = Entity(name="testhasenstall", group=group)
        db.session.add(entity)
        db.session.commit()

        self.assertEqual(group.entity.name, "testhasenstall")

        with self.assertRaises(IntegrityError):
            entity2 = Entity(name="oinkhasenstall", group_id=group.id)
            db.session.add(entity2)
            db.session.commit()

        db.session.rollback()
        self.assertEqual(group.entity.name, "testhasenstall")

    def test_access(self):
        subject = _create_group()
        try_admin = _create_user("admin.hase", is_admin=True)
        try_normal = _create_user("normal.hase")
        try_other = _create_user("other.hase")

        self.assertTrue(subject.check_access(try_admin))
        self.assertFalse(subject.check_access(try_normal))
        self.assertFalse(subject.check_access(try_other))

        ug = UserGroup(user=try_normal, group=subject)
        db.session.add(ug)
        db.session.commit()

        self.assertTrue(subject.check_access(try_normal))
        self.assertFalse(subject.check_access(try_other))

    def test_access_owner(self):
        try_normal = _create_user("normal.hase", is_admin=False)
        subject = _create_group()

        self.assertFalse(subject.check_access(try_normal))
        subject.owner = try_normal
        self.assertTrue(subject.check_access(try_normal))

    def test_update_access(self):
        subject = _create_group()
        try_admin = _create_user("admin.hase", is_admin=True)
        try_normal = _create_user("normal.hase")

        self.assertTrue(subject.check_update_access(try_admin))
        self.assertFalse(subject.check_update_access(try_normal))

        ug = UserGroup(user=try_normal, group=subject)
        db.session.add(ug)
        db.session.commit()
        for allow in [GroupRoles.admin]:
            ug.role = allow
            db.session.commit()
            self.assertTrue(subject.check_update_access(try_normal))
        for deny in [GroupRoles.contributor, GroupRoles.readonly]:
            ug.role = deny
            db.session.commit()
            self.assertFalse(subject.check_update_access(try_normal))

    def test_update_access_owner(self):
        subject = _create_group()
        try_normal = _create_user("normal.hase", is_admin=False)
        self.assertFalse(subject.check_update_access(try_normal))

        subject.owner = try_normal
        self.assertTrue(subject.check_update_access(try_normal))

    def test_schema(self):
        schema = GroupSchema()
        group = _create_group()
        group.quota = 999

        serialized = typing.cast(dict, schema.dump(group))
        self.assertEqual(serialized["id"], str(group.id))
        self.assertEqual(serialized["quota"], group.quota)
        self.assertEqual(serialized["used_quota"], 0)
        self.assertEqual(serialized["image_count"], 0)

        self.assertIsNone(serialized["entityRef"])

        self.assertFalse(serialized["deleted"])
        self.assertIsNone(serialized["deletedAt"])

    def test_schema_entity(self):
        schema = GroupSchema()
        group = _create_group()
        entity = Entity(name="testhasenstall", group=group)
        db.session.add(entity)
        db.session.commit()

        serialized = typing.cast(dict, schema.dump(group))
        self.assertEqual(serialized["entityRef"], entity.name)

    def test_schema_users(self):
        schema = GroupSchema()
        user = _create_user()
        group = _create_group()
        group.users.append(UserGroup(user=user, group=group, role=GroupRoles.readonly))
        db.session.commit()

        serialized = typing.cast(dict, schema.dump(group))
        self.assertEqual(serialized["users"][0]["user"]["id"], str(user.id))
        self.assertEqual(serialized["users"][0]["user"]["username"], user.username)
        self.assertEqual(serialized["users"][0]["role"], str(GroupRoles.readonly))

    def test_deserialize(self):
        schema = GroupSchema()

        deserialized = typing.cast(
            dict,
            schema.load(
                {
                    "name": "Testhasenstall",
                    "email": "test@ha.se",
                    "quota": 666,
                }
            ),
        )
        self.assertEqual(deserialized["name"], "Testhasenstall")
        self.assertEqual(deserialized["quota"], 666)

    def test_default_quota(self):
        old_default = self.app.config["DEFAULT_GROUP_QUOTA"]
        self.app.config["DEFAULT_GROUP_QUOTA"] = 1234
        group = _create_group("Testhase2")
        self.assertEqual(group.quota, self.app.config["DEFAULT_GROUP_QUOTA"])
        db.session.add(group)
        db.session.commit()

        read_group = Group.query.filter_by(name="Testhase2").one()
        self.assertEqual(group.quota, self.app.config["DEFAULT_GROUP_QUOTA"])

        self.app.config["DEFAULT_GROUP_QUOTA"] = old_default

    def test_quota(self):
        group = _create_group("Testhase2")
        group.quota = 666
        db.session.add(group)
        db.session.commit()

        read_group = Group.query.filter_by(name="Testhase2").one()
        self.assertEqual(read_group.quota, 666)

    def test_image_count(self):
        group = _create_group()
        db.session.add(group)
        db.session.commit()

        # no entity
        self.assertEqual(group.image_count, 0)

        entity = Entity(name=default_entity_name, group=group)
        self.assertEqual(group.image_count, 0)

        image1 = _create_image(postfix="1", uploadState=UploadStates.completed)[0]
        self.assertEqual(group.image_count, 1)

        # only completed counts
        image2_broken = _create_image(postfix="2_broken", uploadState=UploadStates.broken)[0]
        self.assertEqual(group.image_count, 1)

        image3 = _create_image(postfix="3", uploadState=UploadStates.completed)
        self.assertEqual(group.image_count, 2)

    def test_used_quota_null(self):
        group = _create_group()
        self.assertEqual(group.calculate_used(), 0)
        self.assertEqual(group.used_quota, 0)

        entity = Entity(name=default_entity_name, group=group)

        image1 = _create_image(postfix="1")[0]
        image1.size = None
        image1.uploadState = UploadStates.completed
        self.assertEqual(group.calculate_used(), 0)

    def test_used_quota(self):
        # quota calc is forwarded to entity, test
        # here nevertheless
        group = _create_group()
        entity = Entity(name=default_entity_name, group=group)

        image1 = _create_image(postfix="1")[0]
        image1.size = 200
        image1.location = "/da/ham1"
        image1.uploadState = UploadStates.completed

        self.assertEqual(group.calculate_used(), 200)
        self.assertEqual(group.used_quota, 200)
        self.assertEqual(entity.used_quota, 200)

        # add second image
        image2 = _create_image(postfix="2")[0]
        image2.size = 300
        image2.location = "/da/ham2"
        image2.uploadState = UploadStates.completed

        self.assertEqual(group.calculate_used(), 500)
        self.assertEqual(group.used_quota, 500)

        # add reference to existing image
        # does not count towards quota
        image2_same = _create_image(postfix="2_same")[0]
        image2_same.size = 400
        image2_same.location = "/da/ham2"
        image2_same.uploadState = UploadStates.completed

        self.assertEqual(group.calculate_used(), 500)
        self.assertEqual(group.used_quota, 500)

        # invalid upload state
        # does not count towards quota
        image3_invalid = _create_image(postfix="3_invalid")[0]
        image3_invalid.size = 500
        image3_invalid.location = "/da/ham3"
        image3_invalid.uploadState = UploadStates.broken

        self.assertEqual(group.calculate_used(), 500)
        self.assertEqual(group.used_quota, 500)
