from Hinkskalle.models.Entity import Entity
import datetime
import os
from tempfile import mkdtemp
from sqlalchemy import update

from Hinkskalle.models import Collection, Image, Tag, Container, UploadStates
from Hinkskalle import db

from ..route_base import RouteBase
from .._util import _create_image, _create_container, _get_json_data


class TestImages(RouteBase):
    def test_list_noauth(self):
        ret = self.client.get("/v1/containers/what/ev/er/images")
        self.assertEqual(ret.status_code, 401)

    def test_list(self):
        image1, container, collection, entity = _create_image("img1")
        image2 = _create_image("img2")[0]
        image2.container_ref = container
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
        self.assertEqual(ret.status_code, 200)
        json = _get_json_data(ret)
        self.assertListEqual([c["id"] for c in json], [str(image1.id), str(image2.id)])

    def test_list_hide(self):
        image1, container, collection, entity = _create_image("img1")
        image2 = _create_image("img2")[0]
        image2.container_ref = container
        image2.hide = True
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
        self.assertEqual(ret.status_code, 200)
        json = _get_json_data(ret)
        self.assertListEqual([c["id"] for c in json], [str(image1.id)])

    def test_list_user(self):
        image1, container, collection, entity = _create_image("img1")
        image2 = _create_image("img2")[0]
        image2.container_ref = container
        container.owner = self.user
        collection.owner = self.user
        entity.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
        self.assertEqual(ret.status_code, 200)
        json = _get_json_data(ret)
        self.assertListEqual([c["id"] for c in json], [str(image1.id), str(image2.id)])

    def test_list_user_other_own_collection(self):
        image1, container, collection, entity = _create_image("img1")
        container.owner = self.other_user
        collection.owner = self.user
        entity.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
        self.assertEqual(ret.status_code, 200)

    def test_list_user_other(self):
        image1, container, collection, entity = _create_image("img1")
        container.owner = self.other_user
        collection.owner = self.other_user
        entity.owner = self.other_user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
        self.assertEqual(ret.status_code, 403)

    def test_get_latest(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))
        self.assertListEqual(data["tags"], ["latest"])
        self.assertFalse(data["canEdit"])

    def test_get_not_sif(self):
        image = _create_image(media_type="pr0n")[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        ret = self.client.get(
            f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}",
            headers={"User-Agent": "Singularity/3.7.3 (Darwin amd64) Go/1.13.3"},
        )
        self.assertEqual(ret.status_code, 406)

        ret = self.client.get(
            f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}",
            headers={"User-Agent": "lynx"},
        )
        self.assertEqual(ret.status_code, 200)

    def test_get_case(self):
        image, container, collection, entity = _create_image()
        db.session.execute(update(Container).where(Container.id == container.id).values(name="oInK"))
        db.session.execute(update(Collection).where(Collection.id == collection.id).values(name="oInK"))
        db.session.execute(update(Entity).where(Entity.id == entity.id).values(name="oInK"))
        db.session.expire_all()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(f"/v1/images/oInK/OiNk/oiNK")
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(_get_json_data(ret)["id"], str(image.id))

    def test_get_private(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        container.private = True
        db.session.commit()

        ret = self.client.get(f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}")
        self.assertEqual(ret.status_code, 403)

        with self.fake_auth():
            ret = self.client.get(f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}")
            self.assertEqual(ret.status_code, 403)

        with self.fake_admin_auth():
            ret = self.client.get(f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}")
            self.assertEqual(ret.status_code, 200)

    def test_get_private_own(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        container.owner = self.user
        container.private = True
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}")
            self.assertEqual(ret.status_code, 200)
        self.assertTrue(_get_json_data(ret)["canEdit"])

    def test_get_default_entity(self):
        image, _, _, entity = _create_image()
        entity.name = "default"
        db.session.commit()

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.commit()

        ret = self.client.get(f"/v1/images//{image.collectionName}/{image.containerName}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""), rf"/v1/images/default/{image.collectionName}/{image.containerName}$"
        )

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

    def test_get_default_entity_single(self):
        image, _, _, entity = _create_image()
        entity.name = "default"
        db.session.commit()

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.commit()

        ret = self.client.get(f"/v1/images/{image.collectionName}/{image.containerName}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

    def test_get_default_collection(self):
        image, _, collection, entity = _create_image()
        collection.name = "default"
        db.session.commit()

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(f"/v1/images/{image.entityName}//{image.containerName}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""), rf"/v1/images/{image.entityName}/default/{image.containerName}$"
        )

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

    def test_get_default_collection_default_entity(self):
        image, _, collection, entity = _create_image()
        entity.name = "default"
        collection.name = "default"
        db.session.commit()

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(f"/v1/images///{image.containerName}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(ret.headers.get("Location", ""), rf"/v1/images/default//{image.containerName}$")
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(ret.headers.get("Location", ""), rf"/v1/images/default/default/{image.containerName}$")

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

        ret = self.client.get(f"/v1/images//{image.containerName}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(ret.headers.get("Location", ""), rf"/v1/images/default/{image.containerName}$")

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

        ret = self.client.get(f"/v1/images/{image.containerName}")
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image.id))

    def test_get_with_tag(self):
        v1_image = _create_image()[0]
        v1_tag = Tag(name="v1", image_ref=v1_image)
        db.session.add(v1_tag)
        db.session.commit()

        latest_image = _create_image(hash="sha256.moo")[0]
        latest_tag = Tag(name="latest", image_ref=latest_image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(
            f"/v1/images/{v1_image.entityName}/{v1_image.collectionName}/{v1_image.containerName}:{v1_tag.name}"
        )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(v1_image.id))
        self.assertListEqual(data["tags"], ["v1"])

    def test_get_hash(self):
        first_image = _create_image(hash="sha256.oink")[0]
        _create_image(hash="sha256.moo")

        ret = self.client.get(
            f"/v1/images/{first_image.entityName}/{first_image.collectionName}/{first_image.containerName}:{first_image.hash}"
        )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(first_image.id))

    def test_get_hash_not_found(self):
        first_image = _create_image(hash="sha256.oink")[0]
        db.session.commit()

        ret = self.client.get(
            f"/v1/images/{first_image.entityName}/{first_image.collectionName}/{first_image.containerName}:sha256.muh"
        )
        self.assertEqual(ret.status_code, 404)

    def test_reset_uploaded(self):
        image = _create_image()[0]
        image.location = "/some/where"
        image.uploadState = UploadStates.completed
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        ret = self.client.get(
            f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
        )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["uploadState"], UploadStates.broken.value)
        read_image = Image.query.get(image.id)
        self.assertEqual(read_image.location, "/some/where")

        image.location = None
        image.uploadState = UploadStates.completed
        db.session.commit()
        ret = self.client.get(
            f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
        )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["uploadState"], UploadStates.broken.value)

    def test_get_arch(self):
        image1 = _create_image()[0]
        image1.arch = "c64"
        image1_tag = Tag(name="v1", image_ref=image1)
        db.session.add(image1_tag)

        image2 = Image(arch="amige", hash="sha256.moo", container_ref=image1.container_ref)
        image2_tag = Tag(name="v1", image_ref=image2)
        db.session.add(image2_tag)
        db.session.commit()

        ret = self.client.get(
            f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:{image1_tag.name}"
        )
        self.assertEqual(ret.status_code, 404)

        ret = self.client.get(
            f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:{image1_tag.name}?arch=c64"
        )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image1.id))
        self.assertListEqual(data["tags"], ["v1"])

    def test_get_default_arch(self):
        image1 = _create_image()[0]
        image1.arch = self.app.config["DEFAULT_ARCH"]
        image1_tag = Tag(name="v1", image_ref=image1)
        db.session.add(image1_tag)

        image2 = Image(arch="amige", hash="sha256.moo", container_ref=image1.container_ref)
        image2_tag = Tag(name="v1", image_ref=image2)
        db.session.add(image2_tag)
        db.session.commit()

        ret = self.client.get(
            f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:{image1_tag.name}"
        )

        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["id"], str(image1.id))
        self.assertListEqual(data["tags"], ["v1"])

    def test_create_noauth(self):
        ret = self.client.post("/v1/images")
        self.assertEqual(ret.status_code, 401)

    def test_create(self):
        container, _, _ = _create_container()
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                },
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["hash"], "sha256.oink")
        self.assertEqual(data["container"], str(container.id))
        self.assertEqual(data["createdBy"], self.admin_username)
        self.assertTrue(data["canEdit"])

    def test_create_singularity(self):
        container, _, _ = _create_container()
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "deleted": False,
                    "createdBy": "",
                    "createdAt": "0001-01-01T00:00:00Z",
                    "updatedAt": "0001-01-01T00:00:00Z",
                    "deletedAt": "0001-01-01T00:00:00Z",
                    "id": "",
                    "hash": "sha256.c032321b292ab9ec25cdd4e4b57bba979629a24c35c97bb034898fc06472145d",
                    "description": "",
                    "container": str(container.id),
                    "size": 0,
                    "uploaded": False,
                    "customData": "",
                    "containerStars": 0,
                    "containerDownloads": 0,
                },
            )
        self.assertEqual(ret.status_code, 200)

    def test_create_readonly(self):
        container, _, _ = _create_container()
        container.readOnly = True
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                },
            )
        self.assertEqual(ret.status_code, 406)

    def test_create_uploaded(self):
        container, _, _ = _create_container()
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                    "uploadState": UploadStates.completed.value,
                },
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["uploadState"], UploadStates.completed.value)
        db_container = Container.query.get(container.id)
        self.assertDictEqual(db_container.imageTags, {"latest": data["id"]})
        self.assertDictEqual(db_container.archImageTags, {"amd64": {"latest": data["id"]}})
        db_image = Image.query.get(data["id"])
        self.assertEqual(db_image.arch, "amd64")

    def test_create_not_unique(self):
        image, container, _, _ = _create_image()
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": image.hash,
                    "container": str(container.id),
                },
            )
        self.assertEqual(ret.status_code, 412)

    def test_invalid_container(self):
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": -666,
                },
            )
        self.assertEqual(ret.status_code, 400)

    def test_reuse_image(self):
        image, _, _, _ = _create_image()
        image.uploadState = UploadStates.completed
        image.location = __file__
        image.size = 999
        db.session.commit()
        image_id = image.id
        other_container, _, _ = _create_container()
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": image.hash,
                    "container": str(other_container.id),
                },
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["uploadState"], UploadStates.completed.value)

        db_image = Image.query.get(image_id)
        self.assertEqual(data["size"], db_image.size)

        other_image = Image.query.get(data["id"])
        self.assertEqual(other_image.location, db_image.location)
        other_db_container = Container.query.get(other_container.id)
        self.assertDictEqual(other_db_container.imageTags, {"latest": str(other_image.id)})

    def test_reuse_image_not_uploaded(self):
        image, _, _, _ = _create_image()
        image.uploadState = UploadStates.initialized
        image.location = __file__
        db.session.commit()
        other_container, _, _ = _create_container()
        other_container_id = other_container.id
        with self.fake_admin_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": image.hash,
                    "container": str(other_container_id),
                },
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertEqual(data["uploadState"], UploadStates.initialized.value)
        self.assertIsNone(data["size"])
        self.assertDictEqual(Container.query.get(other_container_id).imageTags, {})

    def test_create_user(self):
        container, coll, entity = _create_container()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                },
            )
        self.assertEqual(ret.status_code, 200)

    def test_create_user_expiresAt(self):
        container, coll, entity = _create_container()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.user
        db.session.commit()

        exp = datetime.datetime.now()
        with self.fake_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                    "expiresAt": exp.isoformat(),
                },
            )
        self.assertEqual(ret.status_code, 200)
        db_image = Image.query.get(_get_json_data(ret)["id"])
        self.assertEqual(db_image.expiresAt, exp)

    def test_create_user_other(self):
        container, coll, entity = _create_container()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.other_user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(
                "/v1/images",
                json={
                    "hash": "sha256.oink",
                    "container": str(container.id),
                },
            )
        self.assertEqual(ret.status_code, 403)

    def test_update_tags(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}/tags",
                json={"tags": ["oink", "grunz"]},
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"tags": ["oink", "grunz"]})

        dbImage = Image.query.get(image.id)
        self.assertListEqual(dbImage.tags, ["oink", "grunz"])

    def test_udpate_tags_remove(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}/tags",
                json={"tags": ["grunz"]},
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"tags": ["grunz"]})

        dbImage = Image.query.get(image.id)
        self.assertListEqual(dbImage.tags, ["grunz"])

    def test_update_tags_existing(self):
        image, container, _, _ = _create_image()

        other_image = Image(container_ref=container, hash="otherhash")
        db.session.add(other_image)
        latest_tag = Tag(name="oink", image_ref=other_image)
        db.session.add(latest_tag)
        db.session.commit()
        other_image_id = other_image.id

        with self.fake_admin_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}/tags",
                json={"tags": ["oink"]},
            )
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertDictEqual(data, {"tags": ["oink"]})

        dbImage = Image.query.get(image.id)
        self.assertListEqual(dbImage.tags, ["oink"])

        otherDbImage = Image.query.get(other_image_id)
        self.assertListEqual(otherDbImage.tags, [])

    def test_update_tags_user(self):
        image = _create_image()[0]
        image.container_ref.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}/tags",
                json={"tags": ["oink"]},
            )
        self.assertEqual(ret.status_code, 200)

    def test_update_tags_user_other(self):
        image = _create_image()[0]

        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}/tags",
                json={"tags": ["oink"]},
            )
        self.assertEqual(ret.status_code, 403)

    def test_update(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                },
            )
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(_get_json_data(ret)["canEdit"])

        dbImage = Image.query.get(image.id)
        self.assertEqual(dbImage.description, "Mei Huat")
        self.assertEqual(dbImage.customData, "hot drei Eckn")

        self.assertTrue(abs(dbImage.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=2))

    def test_update_dumponly(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()
        image_id = image.id

        with self.fake_admin_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "hash": "hasch",
                    "blob": "blubb",
                    "container": "222",
                },
            )
        self.assertEqual(ret.status_code, 200)

        dbImage: Image = Image.query.get(image_id)
        self.assertEqual(dbImage.hash, image.hash)
        self.assertEqual(dbImage.blob, image.blob)
        self.assertEqual(dbImage.container, image.container)

    def test_update_user(self):
        image = _create_image()[0]
        image.container_ref.owner = self.user
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                },
            )
        self.assertEqual(ret.status_code, 200)

    def test_update_user_expiresAt(self):
        image = _create_image()[0]
        image.owner = self.user
        image.container_ref.owner = self.user
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()
        image_id = image.id

        exp = datetime.datetime.now()
        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                    "expiresAt": exp.isoformat(),
                },
            )
        self.assertEqual(ret.status_code, 200)
        db_image = Image.query.get(image_id)
        self.assertEqual(db_image.expiresAt, exp)

    def test_update_user_expiresAt_denied(self):
        image = _create_image()[0]
        image.owner = self.admin_user
        image.container_ref.owner = self.user
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        exp = datetime.datetime.now()
        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                    "expiresAt": exp.isoformat(),
                },
            )
        self.assertEqual(ret.status_code, 403)

    def test_update_user_expiresAt_unchanged(self):
        exp = datetime.datetime.now()
        image = _create_image(expiresAt=exp)[0]
        image.owner = self.admin_user
        image.container_ref.owner = self.user
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                    "expiresAt": exp.isoformat(),
                },
            )
        self.assertEqual(ret.status_code, 200)

    def test_update_user_other(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_auth():
            ret = self.client.put(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:oink",
                json={
                    "description": "Mei Huat",
                    "customData": "hot drei Eckn",
                },
            )
        self.assertEqual(ret.status_code, 403)

    def test_delete(self):
        image = _create_image()[0]
        self._fake_uploaded_image(image)

        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(Image.query.get(image.id))
        self.assertFalse(os.path.exists(image.location))

    def test_delete_quota(self):
        image, _, _, entity = _create_image()
        entity_id = entity.id
        self._fake_uploaded_image(image)
        image.size = 100
        entity.calculate_used()
        db.session.commit()

        self.assertEqual(entity.used_quota, 100)
        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 200)
        entity = Entity.query.get(entity_id)
        self.assertEqual(entity.used_quota, 0)

    def test_delete_file_ref(self):
        image = _create_image(postfix="polarbear")[0]
        other_image = _create_image(postfix="penguin")[0]
        self._fake_uploaded_image(image)
        other_image.location = image.location
        other_image.uploadState = UploadStates.completed
        other_image_id = other_image.id
        db.session.commit()
        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 200)
        db_img = Image.query.get(other_image_id)
        self.assertTrue(os.path.exists(db_img.location))

    def test_delete_with_tags(self):
        image = _create_image()[0]
        latest_tag = Tag(name="oink", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(Image.query.get(image.id))

    def test_delete_arch(self):
        image1, container, _, _ = _create_image()
        container.tag_image("v1", image1.id, arch="c64")
        image2 = Image(hash="other-image-2", container_ref=container)
        db.session.add(image2)
        db.session.commit()
        image2_id = image2.id
        image1_id = image1.id
        container.tag_image("v1", image2.id, arch="amiga")

        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:v1"
            )
        self.assertEqual(ret.status_code, 404)

        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:v1?arch=c64"
            )

        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(Image.query.get(image1_id))
        self.assertIsNotNone(Image.query.get(image2_id))

    def test_delete_default_arch(self):
        image1, container, _, _ = _create_image()
        container.tag_image("v1", image1.id, arch=self.app.config["DEFAULT_ARCH"])
        image2 = Image(hash="other-image-2", container_ref=container)
        db.session.add(image2)
        db.session.commit()
        image2_id = image2.id
        image1_id = image1.id
        container.tag_image("v1", image2.id, arch="amiga")

        with self.fake_admin_auth():
            ret = self.client.delete(
                f"/v1/images/{image1.entityName}/{image1.collectionName}/{image1.containerName}:v1"
            )

        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(Image.query.get(image1_id))
        self.assertIsNotNone(Image.query.get(image2_id))

    def test_delete_user(self):
        image = _create_image()[0]
        image.container_ref.owner = self.user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(Image.query.get(image.id))

    def test_delete_user_other(self):
        image = _create_image()[0]
        image.container_ref.owner = self.other_user
        db.session.commit()

        with self.fake_auth():
            ret = self.client.delete(
                f"/v1/images/{image.entityName}/{image.collectionName}/{image.containerName}:{image.hash}"
            )
        self.assertEqual(ret.status_code, 403)

    def _fake_uploaded_image(self, image):
        self.app.config["IMAGE_PATH"] = mkdtemp()
        img_base = os.path.join(self.app.config["IMAGE_PATH"], "_imgs")
        os.makedirs(img_base, exist_ok=True)
        image.uploadState = UploadStates.completed
        image.location = os.path.join(img_base, "testhase.sif")
        db.session.commit()
        with open(image.location, "w") as outfh:
            outfh.write("I am Testhase!")
