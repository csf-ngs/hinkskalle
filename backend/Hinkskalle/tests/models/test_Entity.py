from datetime import datetime, timedelta
import typing

from Hinkskalle.models.Entity import Entity, EntitySchema
from Hinkskalle.models.Collection import Collection
from Hinkskalle import db
from Hinkskalle.models.Image import UploadStates
from Hinkskalle.models.User import GroupRoles
from ..model_base import ModelBase
from .._util import _create_user, _create_image, _create_group, _set_member, default_entity_name


class TestEntity(ModelBase):
    def test_entity(self):
        entity = Entity(name=default_entity_name)
        db.session.add(entity)
        db.session.commit()

        read_entity = Entity.query.filter_by(name=default_entity_name).first()
        self.assertEqual(read_entity.id, entity.id)
        self.assertTrue(abs(read_entity.createdAt - datetime.now()) < timedelta(seconds=2))

    def test_entity_case(self):
        entity = Entity(name="TestHase")
        db.session.add(entity)
        db.session.commit()

        read_entity = Entity.query.get(entity.id)
        self.assertEqual(read_entity.name, "testhase")

    def test_count(self):
        ent = Entity(name=default_entity_name)
        self.assertEqual(ent.size, 0)
        db.session.add(ent)
        db.session.commit()
        self.assertEqual(ent.size, 0)

        coll1 = Collection(name="coll_i", entity_ref=ent)
        db.session.add(coll1)
        db.session.commit()
        self.assertEqual(ent.size, 1)

        other_ent = Entity(name="other-hase")
        db.session.add(other_ent)
        db.session.commit()
        other_coll = Collection(name="coll_other", entity_ref=other_ent)
        db.session.add(other_coll)
        db.session.commit()

        self.assertEqual(ent.size, 1)

    def test_used_quota_null(self):
        ent = Entity(name="test-quota")
        self.assertEqual(ent.calculate_used(), 0)
        self.assertEqual(ent.used_quota, 0)

        image1 = _create_image(postfix="1")[0]
        image1.container_ref.collection_ref.entity_ref = ent
        image1.size = None
        image1.uploadState = UploadStates.completed
        self.assertEqual(ent.calculate_used(), 0)

    def test_used_quota(self):
        ent = Entity(name="test-quota")
        self.assertEqual(ent.calculate_used(), 0)
        self.assertEqual(ent.used_quota, 0)

        # count one image
        image1 = _create_image(postfix="1")[0]
        image1.container_ref.collection_ref.entity_ref = ent
        image1.size = 200
        image1.location = "/da/ham1"
        image1.uploadState = UploadStates.completed

        self.assertEqual(ent.calculate_used(), 200)
        self.assertEqual(ent.used_quota, 200)
        self.assertEqual(image1.container_ref.used_quota, 200)
        self.assertEqual(image1.container_ref.collection_ref.used_quota, 200)

        # add second image
        image2 = _create_image(postfix="2")[0]
        image2.container_ref.collection_ref.entity_ref = ent
        image2.size = 300
        image2.location = "/da/ham2"
        image2.uploadState = UploadStates.completed

        self.assertEqual(ent.calculate_used(), 500)
        self.assertEqual(image2.container_ref.used_quota, 300)
        self.assertEqual(image2.container_ref.collection_ref.used_quota, 300)

        # add reference to existing image to a different
        # collection - entity usage stays same, collection
        # usage counts normal
        image2_same = _create_image(postfix="2_same")[0]
        image2_same.container_ref.collection_ref.entity_ref = ent
        image2_same.size = 400
        image2_same.location = "/da/ham2"
        image2_same.uploadState = UploadStates.completed

        self.assertEqual(ent.calculate_used(), 500)
        self.assertEqual(image2_same.container_ref.used_quota, 400)
        self.assertEqual(image2_same.container_ref.collection_ref.used_quota, 400)

        # another reference, same collection, different container
        # should not add to entity nor collection, but to container
        image3 = _create_image(postfix="3")[0]
        image3.container_ref.collection_ref = image2_same.container_ref.collection_ref
        image3.size = 600
        image3.location = "/da/ham2"
        image3.uploadState = UploadStates.completed

        self.assertEqual(ent.calculate_used(), 500)
        self.assertEqual(image3.container_ref.used_quota, 600)
        self.assertEqual(image3.container_ref.collection_ref.used_quota, 400)

        # invalid upload state - do not count this image
        image4_upl = _create_image(postfix="4")[0]
        image4_upl.container_ref.collection_ref.entity_ref = ent
        image4_upl.size = 300
        image4_upl.location = "/da/ham3"
        image4_upl.uploadState = UploadStates.broken

        self.assertEqual(ent.calculate_used(), 500)
        self.assertEqual(image4_upl.container_ref.used_quota, 0)
        self.assertEqual(image4_upl.container_ref.collection_ref.used_quota, 0)

    def test_access(self):
        admin = _create_user(name="admin.oink", is_admin=True)
        user = _create_user(name="user.oink", is_admin=False)
        entity = Entity(name=default_entity_name)
        self.assertTrue(entity.check_access(admin))
        self.assertFalse(entity.check_access(user))
        entity.owner = user
        self.assertTrue(entity.check_access(user))

        default = Entity(name="default")
        self.assertTrue(default.check_access(user))

    def test_update_access(self):
        admin = _create_user(name="admin.oink", is_admin=True)
        user = _create_user(name="user.oink", is_admin=False)
        entity = Entity(name=default_entity_name)

        self.assertTrue(entity.check_update_access(admin))
        self.assertFalse(entity.check_update_access(user))

        entity.owner = user
        self.assertTrue(entity.check_update_access(user))

        default = Entity(name="default")
        self.assertFalse(default.check_update_access(user))

    def test_group_access(self):
        user = _create_user(name="user.oink", is_admin=False)
        group = _create_group(name="Oinkhasenstall")
        entity = Entity(name=default_entity_name, group=group)

        self.assertFalse(entity.check_access(user))
        ug = _set_member(user, group)
        for role in [GroupRoles.admin, GroupRoles.contributor, GroupRoles.readonly]:
            ug.role = role
            self.assertTrue(entity.check_access(user))

    def test_group_update_access(self):
        user = _create_user(name="user.oink", is_admin=False)
        group = _create_group(name="Oinkhasenstall")
        entity = Entity(name=default_entity_name, group=group)

        self.assertFalse(entity.check_update_access(user))

        ug = _set_member(user, group)
        for role in [GroupRoles.admin, GroupRoles.contributor]:
            ug.role = role
            self.assertTrue(entity.check_update_access(user))
        for role in [GroupRoles.readonly]:
            ug.role = role
            self.assertFalse(entity.check_update_access(user))

    def test_schema(self):
        entity = Entity(name="Test Hase")
        db.session.add(entity)
        db.session.commit()
        schema = EntitySchema()
        serialized = typing.cast(dict, schema.dump(entity))
        self.assertEqual(serialized["id"], str(entity.id))
        self.assertEqual(serialized["name"], entity.name)
        self.assertFalse(serialized["canEdit"])

        self.assertIsNone(serialized["deletedAt"])
        self.assertFalse(serialized["deleted"])

        self.assertRegex(serialized["createdAt"], r"[+-]?\d\d:\d\d$")

        entity.used_quota = 999
        serialized = typing.cast(dict, schema.dump(entity))
        self.assertEqual(serialized["usedQuota"], 999)

    def test_schema_user(self):
        user = _create_user()
        user.quota = 999
        entity = Entity(name="Testhase", owner=user)
        db.session.add(entity)
        db.session.commit()

        schema = EntitySchema()
        serialized = typing.cast(dict, schema.dump(entity))
        self.assertEqual(serialized["quota"], 999)

    def test_schema_group(self):
        group = _create_group()
        group.quota = 999
        entity = Entity(name="Test Hase", group=group)
        db.session.add(entity)
        db.session.commit()

        schema = EntitySchema()
        serialized = typing.cast(dict, schema.dump(entity))
        self.assertTrue(serialized["isGroup"])
        self.assertEqual(serialized["groupRef"], group.name)
        self.assertEqual(serialized["quota"], 999)

    def test_quota_no_owner(self):
        """entities without owner get unlimited quota"""
        entity = Entity(name="test1hase")
        db.session.add(entity)
        db.session.commit()
        self.assertEqual(entity.quota, 0)

    def test_quota(self):
        user = _create_user("test.hase")
        user.quota = 666
        entity = Entity(name="testhase", owner=user)
        db.session.add(entity)
        db.session.commit()

        self.assertEqual(entity.quota, 666)

        user.quota = 999
        self.assertEqual(entity.quota, 999)

    def test_quota_group(self):
        group = _create_group("Testhasenstall")
        group.quota = 777
        entity = Entity(name="testhase", group=group)
        db.session.add(entity)
        db.session.commit()

        self.assertEqual(entity.quota, 777)

        group.quota = 888
        self.assertEqual(entity.quota, 888)
