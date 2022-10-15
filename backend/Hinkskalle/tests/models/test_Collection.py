from datetime import datetime, timedelta
import typing

from Hinkskalle.models import Collection, CollectionSchema, Container

from Hinkskalle import db
from Hinkskalle.models.User import GroupRoles
from ..model_base import ModelBase
from .._util import _create_user, _create_collection, _create_group, _set_member


class TestCollection(ModelBase):
    def test_collection(self):
        coll, entity = _create_collection()

        read_coll = Collection.query.filter_by(name="test-collection").one()
        self.assertEqual(read_coll.id, coll.id)
        self.assertTrue(abs(read_coll.createdAt - datetime.now()) < timedelta(seconds=2))

        self.assertEqual(read_coll.entity, entity.id)
        self.assertEqual(read_coll.entityName, entity.name)

    def test_collection_case(self):
        coll, _ = _create_collection("TestCollection")
        read_coll = Collection.query.get(coll.id)
        self.assertEqual(read_coll.name, "testcollection")

    def test_count(self):
        coll, entity = _create_collection()
        self.assertEqual(coll.size, 0)
        no_create = Collection(name="no-create", entity_ref=entity)
        self.assertEqual(no_create.size, 0)

        cont1 = Container(name="cont_i", collection_ref=coll)
        db.session.add(cont1)
        db.session.commit()
        self.assertEqual(coll.size, 1)

        other_coll, _ = _create_collection("other")
        other_cont = Container(name="cont_other", collection_ref=other_coll)
        db.session.add(other_cont)
        db.session.commit()

        self.assertEqual(coll.size, 1)

    def test_access(self):
        admin = _create_user(name="admin.oink", is_admin=True)
        user = _create_user(name="user.oink", is_admin=False)
        other_user = _create_user(name="user.muh", is_admin=False)
        coll, entity = _create_collection("other")
        self.assertTrue(coll.check_access(admin))
        self.assertFalse(coll.check_access(user))

        coll, entity = _create_collection("own")
        entity.owner = user
        coll.owner = user
        self.assertTrue(coll.check_access(user))
        coll.owner = other_user
        self.assertTrue(coll.check_access(user))

        coll, entity = _create_collection("own-default")
        entity.owner = other_user
        coll.owner = user
        self.assertTrue(coll.check_access(user))

        coll, default = _create_collection("default")
        default.name = "default"
        coll.owner = user
        self.assertTrue(coll.check_access(user))
        coll.owner = other_user
        self.assertTrue(coll.check_access(user))

    def test_update_access(self):
        admin = _create_user(name="admin.oink", is_admin=True)
        user = _create_user(name="user.oink", is_admin=False)

        coll, _ = _create_collection("other")
        self.assertTrue(coll.check_update_access(admin))
        self.assertFalse(coll.check_update_access(user))

        coll, _ = _create_collection("own")
        coll.owner = user
        self.assertTrue(coll.check_update_access(user))

        coll, default = _create_collection("default")
        default.name = "default"
        db.session.commit()
        self.assertFalse(coll.check_update_access(user))

    def test_group_access(self):
        user = _create_user("user.oink", is_admin=False)
        group = _create_group("Testhasenstall")
        coll, entity = _create_collection("group")
        entity.group = group

        self.assertFalse(coll.check_access(user))

        ug = _set_member(user, group)
        for role in GroupRoles:
            ug.role = role
            self.assertTrue(coll.check_access(user))

    def test_group_access_update(self):
        user = _create_user("user.oink", is_admin=False)
        group = _create_group("Testhasenstall")
        coll, entity = _create_collection("group")
        entity.group = group

        self.assertFalse(coll.check_update_access(user))

        ug = _set_member(user, group)
        for role in [GroupRoles.admin, GroupRoles.contributor]:
            ug.role = role
            self.assertTrue(coll.check_update_access(user))

        for role in [GroupRoles.readonly]:
            ug.role = role
            self.assertFalse(coll.check_update_access(user))

    def test_schema(self):
        schema = CollectionSchema()
        coll, entity = _create_collection()

        serialized = typing.cast(dict, schema.dump(coll))
        self.assertEqual(serialized["id"], str(coll.id))
        self.assertEqual(serialized["name"], coll.name)

        self.assertEqual(serialized["entity"], str(entity.id))
        self.assertEqual(serialized["entityName"], entity.name)

        self.assertIsNone(serialized["deletedAt"])
        self.assertFalse(serialized["deleted"])
