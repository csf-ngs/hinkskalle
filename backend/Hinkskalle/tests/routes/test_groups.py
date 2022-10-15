from pprint import pprint
from ..route_base import RouteBase
from .._util import _create_group, _set_member, _create_user, _create_collection
from Hinkskalle import db
from Hinkskalle.models.User import Group, GroupRoles, UserGroup, User
from Hinkskalle.models.Entity import Entity
from sqlalchemy.orm.exc import NoResultFound  # type: ignore
import datetime
import typing


class TestGroups(RouteBase):
    def test_list_noauth(self):
        ret = self.client.get("/v1/groups")
        self.assertEqual(ret.status_code, 401)

    def test_get_noauth(self):
        ret = self.client.get("/v1/groups/Testhasenstall")
        self.assertEqual(ret.status_code, 401)

    def test_post_noauth(self):
        ret = self.client.post("/v1/groups", json={"name": "Testhasenstall", "email": "stall@testha.se"})
        self.assertEqual(ret.status_code, 401)

    def test_put_noauth(self):
        ret = self.client.put("/v1/groups/Testhasenstall", json={"email": "stall@testha.se"})
        self.assertEqual(ret.status_code, 401)

    def test_delete_noauth(self):
        ret = self.client.delete("/v1/groups/Testhasenstall")
        self.assertEqual(ret.status_code, 401)

    def test_list(self):
        group1 = _create_group("Testhasenstall")
        group2 = _create_group("Kasperltheater")

        with self.fake_admin_auth():
            ret = self.client.get("/v1/groups")

        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertIsInstance(json, list)
        self.assertEqual(len(json), 2)
        self.assertListEqual([g["name"] for g in json], [group2.name, group1.name])

    def test_list_user(self):
        group1 = _create_group("Testhasenstall")
        group2 = _create_group("Kasperltheater")

        _set_member(user=self.user, group=group1)

        with self.fake_auth():
            ret = self.client.get("/v1/groups")

        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertIsInstance(json, list)
        self.assertEqual(len(json), 1)
        self.assertListEqual([g["name"] for g in json], [group1.name])

    def test_list_query(self):
        group1 = _create_group("Testhasenstall")
        group2 = _create_group("Kasperltheater")

        with self.fake_admin_auth():
            ret = self.client.get("/v1/groups?name=hasen")

        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertIsInstance(json, list)
        self.assertEqual(len(json), 1)
        self.assertListEqual([g["name"] for g in json], [group1.name])

        with self.fake_admin_auth():
            ret = self.client.get("/v1/groups?name=kasper")

        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertIsInstance(json, list)
        self.assertEqual(len(json), 1)
        self.assertListEqual([g["name"] for g in json], ["Kasperltheater"])

    def test_list_user_query(self):
        group1 = _create_group("Testhasenstall")
        group2 = _create_group("Kasperltheater")
        _set_member(user=self.user, group=group1)
        with self.fake_auth():
            ret = self.client.get("/v1/groups?name=kasper")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertListEqual(json, [])

    def test_get(self):
        group1 = _create_group("Testhasenstall")

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/groups/{group1.name}")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertDictContainsSubset(
            {
                "id": str(group1.id),
                "name": group1.name,
                "email": group1.email,
                "entityRef": None,
                "canEdit": True,
            },
            json,
        )

    def test_get_entity_ref(self):
        group1 = _create_group("Testhasenstall")

        entity = Entity(name=group1.name, group=group1)
        db.session.add(entity)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/groups/{group1.name}")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertDictContainsSubset(
            {
                "id": str(group1.id),
                "name": group1.name,
                "email": group1.email,
                "entityRef": group1.entity.name,
            },
            json,
        )

    def test_get_members(self):
        group1 = _create_group("Testhasenstall")
        _set_member(group=group1, user=self.user, role=GroupRoles.contributor)

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/groups/{group1.name}")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        members = json.get("users")
        self.assertIsNotNone(members)
        self.assertEqual(len(members), 1)
        self.assertDictContainsSubset({"role": str(GroupRoles.contributor)}, members[0])
        self.assertDictContainsSubset({"username": self.username}, members[0]["user"])

    def test_get_user_member(self):
        group1 = _create_group("Testhasenstall")
        _set_member(self.user, group1)
        with self.fake_auth():
            ret = self.client.get(f"/v1/groups/{group1.name}")
        self.assertEqual(ret.status_code, 200)
        data = ret.get_json().get("data")  # type: ignore
        self.assertEqual(data["id"], str(group1.id))
        self.assertFalse(data["canEdit"])

    def test_get_user_not_member(self):
        group1 = _create_group("Testhasenstall")
        with self.fake_auth():
            ret = self.client.get(f"/v1/groups/{group1.name}")
        self.assertEqual(ret.status_code, 403)

    def test_create(self):
        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
        }
        with self.fake_admin_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)
        data = ret.get_json().get("data")  # type: ignore
        self.assertEqual(data["name"], group_data["name"])
        self.assertEqual(data["entityRef"], group_data["name"].lower())
        self.assertTrue(data["canEdit"])

        db_group = Group.query.get(data["id"])
        self.assertEqual(db_group.name, group_data["name"])
        self.assertEqual(db_group.email, group_data["email"])
        self.assertEqual(db_group.createdBy, self.admin_username)

        try:
            db_entity = Entity.query.filter(Entity.name == data["entityRef"]).one()
        except NoResultFound:
            self.fail("db entity not found")
        self.assertEqual(db_entity.createdBy, self.admin_username)
        self.assertEqual(db_entity.group_id, db_group.id)

    def test_create_slugify(self):
        group_data = {
            "name": "Test h&sen ställ.",
            "email": "some@thi.ng",
        }
        with self.fake_admin_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)
        data = ret.get_json().get("data")  # type: ignore
        self.assertEqual(data["entityRef"], "test-h-sen-stall")
        db_entity = Entity.query.filter(Entity.name == data["entityRef"]).one()

    def test_create_entity_exists(self):
        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
        }
        entity = Entity(name=group_data["name"])
        db.session.add(entity)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 412)

    def test_create_not_unique(self):
        existing = _create_group()
        group_data = {
            "name": existing.name,
            "email": "stall@testha.se",
        }
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 412)

    def test_create_user(self):
        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
        }
        with self.fake_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)
        ret_group = ret.get_json().get("data")  # type: ignore
        self.assertTrue(ret_group["canEdit"])
        db_group = Group.query.get(ret_group["id"])

        self.assertEqual(db_group.createdBy, self.username)
        db_member = db_group.users_sth.join(UserGroup.user).filter(User.username == self.username).one()
        self.assertEqual(db_member.role, GroupRoles.admin)

        db_entity = Entity.query.filter(Entity.name == ret_group["entityRef"]).one()
        self.assertEqual(db_entity.createdBy, self.username)

    def test_create_quota_default(self):
        old_default = self.app.config["DEFAULT_GROUP_QUOTA"]
        self.app.config["DEFAULT_GROUP_QUOTA"] = 1234
        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
        }
        with self.fake_admin_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)

        ret_group = typing.cast(dict, ret.get_json().get("data"))
        self.assertEqual(ret_group["quota"], self.app.config["DEFAULT_GROUP_QUOTA"])

        self.app.config["DEFAULT_GROUP_QUOTA"] = old_default

    def test_create_quota(self):
        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
            "quota": 9876,
        }
        with self.fake_admin_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)

        ret_group = typing.cast(dict, ret.get_json().get("data"))
        self.assertEqual(ret_group["quota"], 9876)

    def test_create_quota_user(self):
        """users cannot set quota of new group, use default"""
        old_default = self.app.config["DEFAULT_GROUP_QUOTA"]
        self.app.config["DEFAULT_GROUP_QUOTA"] = 1234

        group_data = {
            "name": "Testhasenstall",
            "email": "stall@testha.se",
            "quota": 9876,
        }
        with self.fake_auth():
            ret = self.client.post("/v1/groups", json=group_data)
        self.assertEqual(ret.status_code, 200)

        ret_group = typing.cast(dict, ret.get_json().get("data"))
        self.assertEqual(ret_group["quota"], self.app.config["DEFAULT_GROUP_QUOTA"])

        self.app.config["DEFAULT_GROUP_QUOTA"] = old_default

    def test_update(self):
        group = _create_group("Updatestall")
        update_data = {"email": "update@testha.se"}
        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json=update_data)
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(ret.get_json().get("data")["canEdit"])  # type: ignore

        db_group = Group.query.get(group.id)
        self.assertEqual(db_group.email, update_data["email"])
        self.assertTrue(abs(db_group.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))

    def test_update_name(self):
        group = _create_group("Updatestall")
        group_id = group.id
        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json={"name": "oink", "email": "test@testha.se"})
        self.assertEqual(ret.status_code, 200)
        db_group = Group.query.get(group_id)
        self.assertEqual(db_group.name, "oink")

    def test_update_name_change_entity(self):
        group = _create_group("Updatestall")
        entity = Entity(name=group.name, group=group)
        db.session.add(entity)
        db.session.commit()

        entity_id = entity.id
        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json={"name": "oink", "email": group.email})
        self.assertEqual(ret.status_code, 200)

        db_entity = Entity.query.get(entity_id)
        self.assertEqual(db_entity.name, "oink")

    def test_update_name_collision(self):
        group1 = _create_group("Updatestall")
        group2 = _create_group("oink")

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group1.name}", json={"name": group2.name, "email": group1.email})
        self.assertEqual(ret.status_code, 409)

    def test_update_name_entity_collision(self):
        group = _create_group("Updatestall")

        group_entity = Entity(name="updatestall", group=group)
        entity = Entity(name="oink")
        db.session.add(group_entity)
        db.session.add(entity)
        db.session.commit()
        group_id = group.id
        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json={"name": "oink", "email": group.email})
        self.assertEqual(ret.status_code, 409)

        db_group = Group.query.get(group_id)
        self.assertEqual(db_group.name, "Updatestall")

    def test_update_user(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user, role=GroupRoles.admin)

        group_data = {"email": "anders@testha.se"}
        with self.fake_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json=group_data)
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(ret.get_json().get("data")["canEdit"])  # type: ignore
        db_group = Group.query.get(group.id)
        self.assertEqual(db_group.email, group_data["email"])

    def test_update_quota(self):
        group = _create_group("Updatestall")
        group.quota = 9876
        db.session.commit()

        group_data = {
            "email": group.email,
            "quota": 1234,
        }
        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json=group_data)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.get_json().get("data")["quota"], 1234)

    def test_update_quota_user(self):
        group = _create_group("Updatestall")
        group.quota = 9876
        db.session.commit()
        ug = _set_member(group=group, user=self.user, role=GroupRoles.admin)

        group_data = {
            "email": group.email,
            "quota": 1234,
        }
        with self.fake_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json=group_data)
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.get_json().get("data")["quota"], 9876)

    def test_update_user_denied(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user)

        for role in [GroupRoles.readonly, GroupRoles.contributor]:
            ug.role = role
            db.session.commit()

            group_data = {"email": "anders@testha.se"}
            with self.fake_auth():
                ret = self.client.put(f"/v1/groups/{group.name}", json=group_data)
            self.assertEqual(ret.status_code, 403)

    def test_update_user_nomember_denied(self):
        group = _create_group("Updatestall")
        group_data = {"email": "anders@testha.se"}
        with self.fake_auth():
            ret = self.client.put(f"/v1/groups/{group.name}", json=group_data)
        self.assertEqual(ret.status_code, 403)

    def test_update_members_add(self):
        group = _create_group("Updatestall")
        user1 = _create_user("test1.hase")
        user2 = _create_user("test2.hase")

        _set_member(group=group, user=user1, role=GroupRoles.contributor)
        group_id = group.id

        member_json = [
            {"role": str(GroupRoles.contributor), "user": {"username": user1.username}},
            {"role": str(GroupRoles.readonly), "user": {"username": user2.username}},
        ]

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 200)

        db_group = Group.query.get(group_id)
        self.assertCountEqual(
            [{"role": ug.role, "username": ug.user.username} for ug in db_group.users],
            [
                {"role": GroupRoles.contributor, "username": user1.username},
                {"role": GroupRoles.readonly, "username": user2.username},
            ],
        )

    def test_update_members_nonexisting(self):
        group = _create_group("Updatestall")

        member_json = [
            {"role": str(GroupRoles.contributor), "user": {"username": "kasperl"}},
        ]

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 404)

    def test_update_members_ignore_fields(self):
        group = _create_group("Updatestall")

        member_json = [
            {"role": str(GroupRoles.contributor), "user": {"username": self.username, "email": "some@thi.ng"}},
        ]

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 200)

    def test_update_members_remove(self):
        group = _create_group("Updatestall")
        user1 = _create_user("test1.hase")
        user2 = _create_user("test2.hase")

        _set_member(group=group, user=user1, role=GroupRoles.contributor)
        _set_member(group=group, user=user2, role=GroupRoles.readonly)
        group_id = group.id

        member_json = [
            {"role": str(GroupRoles.contributor), "user": {"username": user1.username}},
        ]

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 200)

        db_group = Group.query.get(group_id)
        self.assertCountEqual(
            [{"role": ug.role, "username": ug.user.username} for ug in db_group.users],
            [
                {"role": GroupRoles.contributor, "username": user1.username},
            ],
        )

    def test_update_members_change(self):
        group = _create_group("Updatestall")
        user1 = _create_user("test1.hase")
        user2 = _create_user("test2.hase")

        _set_member(group=group, user=user1, role=GroupRoles.contributor)
        _set_member(group=group, user=user2, role=GroupRoles.readonly)
        group_id = group.id

        member_json = [
            {"role": str(GroupRoles.contributor), "user": {"username": user1.username}},
            {"role": str(GroupRoles.admin), "user": {"username": user2.username}},
        ]

        with self.fake_admin_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 200)

        db_group = Group.query.get(group_id)
        self.assertCountEqual(
            [{"role": ug.role, "username": ug.user.username} for ug in db_group.users],
            [
                {"role": GroupRoles.contributor, "username": user1.username},
                {"role": GroupRoles.admin, "username": user2.username},
            ],
        )

    def test_update_members_user(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user, role=GroupRoles.admin)

        user2 = _create_user("test2.hase")
        group_id = group.id

        member_json = [
            {"role": str(GroupRoles.admin), "user": {"username": self.username}},
            {"role": str(GroupRoles.readonly), "user": {"username": user2.username}},
        ]

        with self.fake_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=member_json)
        self.assertEqual(ret.status_code, 200)

        db_group = Group.query.get(group_id)
        self.assertCountEqual(
            [{"role": ug.role, "username": ug.user.username} for ug in db_group.users],
            [
                {"role": GroupRoles.admin, "username": self.username},
                {"role": GroupRoles.readonly, "username": user2.username},
            ],
        )

    def test_update_members_user_denied(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user)

        for role in [GroupRoles.readonly, GroupRoles.contributor]:
            ug.role = role
            db.session.commit()

            members_json = [{"role": str(role), "user": {"username": self.username}}]
            with self.fake_auth():
                ret = self.client.put(f"/v1/groups/{group.name}/members", json=members_json)
            self.assertEqual(ret.status_code, 403)

    def test_update_members_user_nomember_denied(self):
        group = _create_group("Updatestall")

        members_json = []
        with self.fake_auth():
            ret = self.client.put(f"/v1/groups/{group.name}/members", json=members_json)
        self.assertEqual(ret.status_code, 403)

    def test_delete(self):
        group = _create_group("Updatestall")
        with self.fake_admin_auth():
            ret = self.client.delete(f"/v1/groups/{group.name}")
        self.assertEqual(ret.status_code, 200)

        self.assertIsNone(Group.query.filter(Group.name == "Updatestall").first())

    def test_delete_entity(self):
        group = _create_group("Deletestall")
        entity = Entity(name=group.name, group=group)
        db.session.add(entity)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.delete(f"/v1/groups/{group.name}")
        self.assertEqual(ret.status_code, 200)

        self.assertIsNone(Entity.query.filter(Entity.name == "deletestall").first())

    def test_delete_entity_referenced(self):
        group = _create_group("Deletestall")
        entity = Entity(name=group.name, group=group)
        db.session.add(entity)
        coll = _create_collection()[0]
        coll.entity_ref = entity
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.delete(f"/v1/groups/{group.name}")
        self.assertEqual(ret.status_code, 412)

    def test_delete_user(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user, role=GroupRoles.admin)

        with self.fake_auth():
            ret = self.client.delete(f"/v1/groups/{group.name}")
        self.assertEqual(ret.status_code, 200)

    def test_delete_user_denied(self):
        group = _create_group("Updatestall")
        ug = _set_member(group=group, user=self.user)

        for role in [GroupRoles.contributor, GroupRoles.readonly]:
            ug.role = role
            db.session.commit()

            with self.fake_auth():
                ret = self.client.delete(f"/v1/groups/{group.name}")
            self.assertEqual(ret.status_code, 403)

    def test_delete_user_nomember_denied(self):
        group = _create_group("Updatestall")
        with self.fake_auth():
            ret = self.client.delete(f"/v1/groups/{group.name}")
        self.assertEqual(ret.status_code, 403)
