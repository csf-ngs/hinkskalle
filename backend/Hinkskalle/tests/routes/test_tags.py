import os.path
import os
from tempfile import mkdtemp

from Hinkskalle import db
from Hinkskalle.models.Container import Container
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Image import Image, UploadStates

from ..route_base import RouteBase
from .._util import _create_image, _get_json_data


class TestTags(RouteBase):
    def test_get_noauth(self):
        ret = self.client.get(f"/v1/tags/whatever")
        self.assertEqual(ret.status_code, 401)

    def test_get(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/tags/{container.id}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {})

        container = Container.query.get(container_id)
        container.tag_image("v1.0", image_id)
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/tags/{container_id}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"v1.0": str(image_id)})

        container = Container.query.get(container_id)
        container.tag_image("oink", image_id)
        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/tags/{container_id}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"v1.0": str(image_id), "oink": str(image_id)})

    def test_get_user(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.user
        db.session.commit()

        container.tag_image("v1.0", image.id)
        with self.fake_auth():
            ret = self.client.get(f"/v1/tags/{container.id}")
        self.assertEqual(ret.status_code, 200)

    def test_get_user_other_own_collection(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.other_user
        db.session.commit()

        container.tag_image("v1.0", image.id)
        with self.fake_auth():
            ret = self.client.get(f"/v1/tags/{container.id}")
        self.assertEqual(ret.status_code, 200)

    def test_get_user_other(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.other_user
        coll.owner = self.other_user
        container.owner = self.other_user
        db.session.commit()

        container.tag_image("v1.0", image.id)
        with self.fake_auth():
            ret = self.client.get(f"/v1/tags/{container.id}")
        self.assertEqual(ret.status_code, 403)

    def test_update(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"v1.0": str(image_id)})
        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {"v1.0": str(image_id)})

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container_id}", json={"oink": str(image_id)})
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)

        self.assertDictEqual(data, {"v1.0": str(image_id), "oink": str(image_id)})
        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {"v1.0": str(image_id), "oink": str(image_id)})

    def test_update_case(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"TestHase": str(image.id)})
        self.assertEqual(ret.status_code, 200)
        self.assertDictEqual(_get_json_data(ret), {"testhase": str(image_id)})
        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {"testhase": str(image_id)})

    def test_valid(self):
        image, container, _, _ = _create_image()
        for fail in ["Babsi Streusand", "-oink", "Babsi&Streusand", "oink-"]:
            with self.fake_admin_auth():
                ret = self.client.post(f"/v1/tags/{container.id}", json={fail: str(image.id)})
            self.assertEqual(ret.status_code, 400)

    def test_remove_tag(self):
        image, container, _, _ = _create_image()
        container_id = container.id
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"oink": None})
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {})
        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {})

    def test_remove_tag_case(self):
        image, container, _, _ = _create_image()
        container_id = container.id
        latest_tag = Tag(name="oiNk", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"OInK": None})
        self.assertEqual(ret.status_code, 200)
        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {})

    def test_multiple(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        latest_tag = Tag(name="v2", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.post(
                f"/v1/tags/{container.id}", json={"v3": str(image.id), "latest": str(image.id), "v2": None}
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"v3": str(image_id), "latest": str(image_id)})

        db_container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {"v3": str(image_id), "latest": str(image_id)})

    def test_update_user(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 200)

    def test_update_user_other(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.other_user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 403)

    def test_symlinks(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        self._fake_uploaded_image(image)

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 200)

        db_image = Image.query.get(image_id)
        link_location = os.path.join(
            self.app.config["IMAGE_PATH"],
            self.app.config["DEFAULT_ARCH"],
            db_image.entityName,
            db_image.collectionName,
            f"{db_image.containerName}_v1.0.sif",
        )
        self.assertTrue(os.path.exists(link_location))
        self.assertTrue(os.path.samefile(link_location, db_image.location))

    def test_symlinks_existing(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        self._fake_uploaded_image(image)

        link_location = os.path.join(
            self.app.config["IMAGE_PATH"],
            self.app.config["DEFAULT_ARCH"],
            image.entityName,
            image.collectionName,
            f"{image.containerName}_v1.0.sif",
        )
        os.makedirs(os.path.dirname(link_location), exist_ok=True)
        with open(link_location, "w") as outfh:
            outfh.write("muh")

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(os.path.exists(link_location))
        db_image = Image.query.get(image_id)
        self.assertTrue(os.path.samefile(link_location, db_image.location))

        os.remove(link_location)
        # overwrite dangling links, too
        os.symlink("/oink/oink/gru.nz", link_location)
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container_id}", json={"v1.0": str(image_id)})
        self.assertEqual(ret.status_code, 200)

    def test_symlinks_default_entity(self):
        image, container, _, entity = _create_image()
        image_id = image.id
        self._fake_uploaded_image(image)
        entity.name = "default"
        db.session.commit()

        link_location = os.path.join(
            self.app.config["IMAGE_PATH"],
            self.app.config["DEFAULT_ARCH"],
            image.collectionName,
            f"{image.containerName}_v1.0.sif",
        )

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": str(image.id)})
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(os.path.exists(link_location))
        db_image = Image.query.get(image_id)
        self.assertTrue(os.path.samefile(link_location, db_image.location))

    def test_update_old(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"Tag": "v1", "ImageID": str(image.id)})
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)

        self.assertDictEqual(data, {"v1": str(image_id)})

    def test_update_invalid(self):
        image, container, _, _ = _create_image()
        image_id = image.id
        container_id = container.id
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container.id}", json={"v1.0": "oink"})
        self.assertEqual(ret.status_code, 404)
        invalidid = image_id * -1

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container_id}", json={"v1.0": invalidid})
        self.assertEqual(ret.status_code, 404)

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/tags/{container_id}", json={"bla&...": image_id})
        self.assertEqual(ret.status_code, 400)

    def _fake_uploaded_image(self, image):
        self.app.config["IMAGE_PATH"] = mkdtemp()
        img_base = os.path.join(self.app.config["IMAGE_PATH"], "_imgs")
        os.makedirs(img_base, exist_ok=True)
        image.uploadState = UploadStates.completed
        image.location = os.path.join(img_base, "testhase.sif")
        db.session.commit()
        with open(image.location, "w") as outfh:
            outfh.write("I am Testhase!")
