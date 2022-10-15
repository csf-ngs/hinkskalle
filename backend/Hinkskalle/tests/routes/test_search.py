from email.mime import image
from pprint import pprint
import typing
import unittest

from ..route_base import RouteBase
from .._util import _create_image, _create_container

from Hinkskalle import db
from Hinkskalle.models.Entity import EntitySchema
from Hinkskalle.models.Collection import CollectionSchema
from Hinkskalle.models.Image import ImageSchema
from Hinkskalle.models.Container import ContainerSchema, Container
from Hinkskalle.models.Image import ImageSchema, Image


class TestSearch(RouteBase):
    def test_search_noauth(self):
        ret = self.client.get("/v1/search?value=something")
        self.assertEqual(ret.status_code, 401)

    def test_search_container(self):
        container, _, _ = _create_container()
        container.name = "ptERANodon"
        db.session.commit()

        dpd = typing.cast(dict, ContainerSchema().dump(container))
        dpd["canEdit"] = True
        expected = {"collection": [], "entity": [], "image": [], "container": [dpd]}

        for search in [container.name, container.name[3:6], container.name[3:6].lower()]:
            with self.fake_admin_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

    def test_search_entity(self):
        _, _, entity = _create_container()
        entity.name = "ptERANodon"
        db.session.commit()

        dpd = typing.cast(dict, EntitySchema().dump(entity))
        dpd["canEdit"] = True
        expected = {"collection": [], "entity": [dpd], "image": [], "container": []}

        for search in [entity.name, entity.name[3:6], entity.name[3:6].lower()]:
            with self.fake_admin_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

    def test_search_collection(self):
        _, collection, _ = _create_container()
        collection.name = "ptERANodon"
        db.session.commit()

        dpd = typing.cast(dict, CollectionSchema().dump(collection))
        dpd["canEdit"] = True
        expected = {"collection": [dpd], "entity": [], "image": [], "container": []}

        for search in [collection.name, collection.name[3:6], collection.name[3:6].lower()]:
            with self.fake_admin_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

    def test_search_image(self):
        image1, container, _, _ = _create_image()
        container.name = "anKYLOsaurus"
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = True
        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True
        expected = {
            "container": [con_dpd],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        for search in [container.name, container.name[3:6], container.name[3:6].lower()]:
            with self.fake_admin_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

    def test_search_image_hide(self):
        image1 = _create_image()[0]
        image1.container_ref.name = "Ankylosaurus"
        image2 = _create_image(hash="sha256.bla", media_type="pr0n")[0]
        image2.container_ref = image1.container_ref
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(image1.container_ref))
        con_dpd["canEdit"] = True

        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True

        expected = {
            "container": [con_dpd],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value=ankylo")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertDictEqual(json, expected)

    def test_search_image_not_sif(self):
        image1, container, _, _ = _create_image()
        container_id = container.id
        image1_id = image1.id
        container.name = "anKYLOsaurus"

        image2 = _create_image(hash="sha256.bla", media_type="application/vnd.docker.image.rootfs.diff.tar.gzip")[0]
        image2_id = image2.id
        image2.container_ref = container
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = True

        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True

        expected = {
            "container": [con_dpd],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        for search in [container.name, container.name[3:6], container.name[3:6].lower()]:
            with self.fake_admin_auth():
                ret = self.client.get(
                    f"/v1/search?value={search}", headers={"User-Agent": "Singularity/3.7.3 (Darwin amd64) Go/1.13.3"}
                )
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value={container.name}", headers={"User-Agent": "lynx"})
        container = Container.query.get(container_id)
        image1 = Image.query.get(image1_id)
        image2 = Image.query.get(image2_id)
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore

        img2_dpd = typing.cast(dict, ImageSchema().dump(image2))
        img2_dpd["canEdit"] = True

        self.assertDictEqual(
            json,
            {
                "container": [con_dpd],
                "image": [img2_dpd, img_dpd],
                "entity": [],
                "collection": [],
            },
        )

    def test_search_hash(self):
        image1, container, _, _ = _create_image()
        container.name = "anKYLOsaurus"
        image1.hash = "sha256.tintifaxkasperlkrokodil"
        db.session.commit()

        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True
        expected = {
            "container": [],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        for search in ["tinti", "tiNTIfax"]:
            with self.fake_admin_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            json = ret.get_json().get("data")  # type: ignore
            self.assertDictEqual(json, expected)

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value=krokodil")
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(
            ret.get_json().get("data"),
            {  # type: ignore
                "container": [],
                "image": [],
                "entity": [],
                "collection": [],
            },
        )

    def test_signed(self):
        image1, container1, _, _ = _create_image(postfix="eins")
        image2, container2, _, _ = _create_image(postfix="zwei")
        container1.name = "fintitax1"
        container2.name = "fintitax2"
        image1.signed = True

        db.session.commit()

        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True
        expected = {
            "container": [],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value=fintitax&signed=true")
        self.assertEqual(ret.status_code, 200)
        data = ret.get_json().get("data")  # type: ignore
        self.assertDictEqual(data, expected)

    def test_arch(self):
        image1, container1, _, _ = _create_image(postfix="eins")
        image2, container2, _, _ = _create_image(postfix="zwei")
        container1.name = "fintitax1"
        container2.name = "fintitax2"
        image1.arch = "pocket calculator"

        db.session.commit()

        img_dpd = typing.cast(dict, ImageSchema().dump(image1))
        img_dpd["canEdit"] = True
        expected = {
            "container": [],
            "image": [img_dpd],
            "entity": [],
            "collection": [],
        }
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value=fintitax&arch=pocket+calculator")
        self.assertEqual(ret.status_code, 200)
        data = ret.get_json().get("data")  # type: ignore
        self.assertDictEqual(data, expected)

    def test_all(self):
        image, container, collection, entity = _create_image()
        entity.name = "oink-entity"
        collection.name = "oink-collection"
        container.name = "oink-container"
        db.session.commit()

        coll_dpd = typing.cast(dict, CollectionSchema().dump(collection))
        coll_dpd["canEdit"] = True
        ent_dpd = typing.cast(dict, EntitySchema().dump(entity))
        ent_dpd["canEdit"] = True
        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = True
        img_dpd = typing.cast(dict, ImageSchema().dump(image))
        img_dpd["canEdit"] = True

        expected = {"collection": [coll_dpd], "entity": [ent_dpd], "container": [con_dpd], "image": [img_dpd]}

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?value=oink")
        self.assertEqual(ret.status_code, 200)
        json = ret.get_json().get("data")  # type: ignore
        self.assertDictEqual(json, expected)

    def test_user(self):
        container, collection, entity = _create_container()

        expected = {
            "collection": [],
            "entity": [],
            "container": [],
            "image": [],
        }

        for search in [container.name, collection.name, entity.name]:
            with self.fake_auth():
                ret = self.client.get(f"/v1/search?value={search}")
            self.assertEqual(ret.status_code, 200)
            self.assertDictEqual(ret.get_json().get("data"), expected)  # type: ignore

    def test_user_access(self):
        container, _, entity = _create_container()
        container.name = "testhase"
        entity.name = "default"
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = False

        expected = {"collection": [], "entity": [], "container": [con_dpd], "image": []}

        with self.fake_auth():
            ret = self.client.get(f"/v1/search?value={container.name}")
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(ret.get_json().get("data"), expected)  # type: ignore

    def test_user_access_owned(self):
        container, _, entity = _create_container()
        container.name = "testhase"
        entity.owner = self.user
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = False

        expected = {"collection": [], "entity": [], "container": [con_dpd], "image": []}

        with self.fake_auth():
            ret = self.client.get(f"/v1/search?value={container.name}")
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(ret.get_json().get("data"), expected)  # type: ignore

    def test_description(self):
        container, _, _ = _create_container()
        container.description = "aNkyLOSaurUS"
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = True

        expected = {"collection": [], "entity": [], "container": [con_dpd], "image": []}

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?description={container.description}")
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(ret.get_json().get("data"), expected)  # type: ignore

    def test_description_value(self):
        container, _, _ = _create_container()
        container2, _, _ = _create_container("oink")
        container.description = "aNkyLOSaurUS"
        container2.description = container.description
        db.session.commit()

        con_dpd = typing.cast(dict, ContainerSchema().dump(container))
        con_dpd["canEdit"] = True

        expected = {"collection": [], "entity": [], "container": [con_dpd], "image": []}

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/search?description={container.description}&value={container.name}")
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(ret.get_json().get("data"), expected)  # type: ignore
