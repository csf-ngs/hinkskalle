import os.path
import tempfile
from tempfile import mkdtemp
from datetime import datetime, timedelta

from ..route_base import RouteBase
from .._util import _create_image, _fake_img_file, _prepare_img_data, _create_user, _create_group

from Hinkskalle.models import Image, Tag, Container, UploadStates, User
from Hinkskalle.models.Entity import Entity
from Hinkskalle.routes.imagefiles import _check_quota
from Hinkskalle import db


class TestImagefiles(RouteBase):
    def test_make_filename(self):
        self.app.config["IMAGE_PATH"] = mkdtemp()
        self.app.config["IMAGE_PATH_HASH_LEVEL"] = 2
        image = _create_image(hash="sha256.oink")[0]
        from Hinkskalle.routes.imagefiles import _make_filename

        fn = _make_filename(image)
        self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}/_imgs/o/i/sha256.oink.sif")

        self.app.config["IMAGE_PATH_HASH_LEVEL"] = 99
        fn = _make_filename(image)
        self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}/_imgs/o/i/n/k/sha256.oink.sif")

        self.app.config["IMAGE_PATH_HASH_LEVEL"] = 0
        fn = _make_filename(image)
        self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}/_imgs/sha256.oink.sif")

    def test_pull(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.commit()

        tmpf = _fake_img_file(image)

        ret = self.client.get(
            f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
        )
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello Dorian!")
        db_container = Container.query.get(container.id)
        self.assertEqual(db_container.downloadCount, 1)
        self.assertAlmostEqual(db_container.latestDownload, datetime.now(), delta=timedelta(seconds=2))
        db_image: Image = Image.query.get(image.id)
        self.assertEqual(db_image.downloadCount, 1)
        self.assertEqual(db_image.containerDownloads, 1)
        self.assertAlmostEqual(db_image.latestDownload, datetime.now(), delta=timedelta(seconds=2))
        ret.close()  # avoid unclosed filehandle warning

        # singularity requests with double slash
        ret = self.client.get(
            f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
        )
        self.assertEqual(ret.status_code, 308)

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.data, b"Hello Dorian!")
        db_container = Container.query.get(container.id)
        self.assertEqual(db_container.downloadCount, 2)
        db_image: Image = Image.query.get(image.id)
        self.assertEqual(db_image.downloadCount, 2)
        self.assertEqual(db_image.containerDownloads, 2)
        ret.close()  # avoid unclosed filehandle warning

        ret = self.client.head(
            f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
        )
        db_container = Container.query.get(container.id)
        self.assertEqual(db_container.downloadCount, 2)
        db_image = Image.query.get(image.id)
        self.assertEqual(db_image.downloadCount, 2)

        tmpf.close()

    def test_pull_arch(self):
        image1, container, _, _ = _create_image()
        image1_tag = Tag(name="v1", image_ref=image1, arch="c64")
        image1.arch = "c64"

        image2 = Image(hash="sha256.oink2", container_ref=container, arch="amiga")
        image2_tag = Tag(name="v1", image_ref=image2, arch="amiga")
        db.session.add(image1_tag)
        db.session.add(image2_tag)
        db.session.commit()

        tmpf1 = _fake_img_file(image1, data=b"oink c64/v1")
        tmpf2 = _fake_img_file(image2, data=b"oink amiga/v1")

        ret = self.client.get(
            f"/v1/imagefile/{image1.entityName}/{image1.collectionName}/{image1.containerName}:{image1_tag.name}?arch=c64"
        )
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"oink c64/v1")
        ret.close()

    def test_pull_no_sif(self):
        image = _create_image(media_type="something")[0]
        image_tag = Tag(name="v1", image_ref=image)
        db.session.add(image_tag)
        tmpf1 = _fake_img_file(image, data=b"oink c64/v1")

        ret = self.client.get(
            f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{image_tag.name}"
        )
        self.assertEqual(ret.status_code, 406)

    def test_pull_private_noauth(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.private = True
        db.session.commit()

        tmpf = _fake_img_file(image)
        ret = self.client.get(
            f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
        )
        self.assertEqual(ret.status_code, 403)

    def test_pull_not_uploaded(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.get(
                f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
        self.assertEqual(ret.status_code, 404)

    def test_pull_private(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.private = True
        db.session.commit()

        tmpf = _fake_img_file(image)

        ret = self.client.get(
            f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
        )
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 403)

        with self.fake_auth():
            ret = self.client.get(
                f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
            self.assertEqual(ret.status_code, 308)
            ret = self.client.get(ret.headers.get("Location"))
            self.assertEqual(ret.status_code, 403)

        with self.fake_admin_auth():
            ret = self.client.get(
                f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
            self.assertEqual(ret.status_code, 308)
            ret = self.client.get(ret.headers.get("Location"))
            self.assertEqual(ret.status_code, 200)
        ret.close()

        tmpf.close()

    def test_pull_user(self):
        image, container, collection, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.owner = self.user
        collection.owner = self.user
        db.session.commit()

        tmpf = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
            self.assertEqual(ret.status_code, 308)
            ret = self.client.get(ret.headers.get("Location"))
            self.assertEqual(ret.status_code, 200)
        ret.close()
        tmpf.close()

    def test_pull_user_other(self):
        image, container, collection, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.owner = self.other_user
        collection.owner = self.other_user
        db.session.commit()

        tmpf = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
            self.assertEqual(ret.status_code, 308)
            ret = self.client.get(ret.headers.get("Location"))
            self.assertEqual(ret.status_code, 200)
        ret.close()
        tmpf.close()

    def test_pull_private_own(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.private = True
        container.owner = self.user
        db.session.commit()

        tmpf = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v1/imagefile//{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
            self.assertEqual(ret.status_code, 308)
            ret = self.client.get(ret.headers.get("Location"))
            self.assertEqual(ret.status_code, 200)
        ret.close()

        tmpf.close()

    def test_pull_private_denied(self):
        image, container, _, _ = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)
        container.private = True
        container.owner = self.other_user
        db.session.commit()

        tmpf = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v1/imagefile/{image.entityName}/{image.collectionName}/{image.containerName}:{latest_tag.name}"
            )
        self.assertEqual(ret.status_code, 403)

    def test_pull_default_entity(self):
        image, _, _, entity = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        entity.name = "default"
        db.session.commit()

        tmpf = _fake_img_file(image, b"Hello default Entity!")

        ret = self.client.get(f"/v1/imagefile/{image.collectionName}/{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Entity!")
        ret.close()

        ret = self.client.get(f"/v1/imagefile//{image.collectionName}/{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Entity!")
        ret.close()

        # singularity requests with double slash
        ret = self.client.get(f"/v1/imagefile///{image.collectionName}/{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Entity!")
        ret.close()  # avoid unclosed filehandle warning
        tmpf.close()

    def test_pull_default_collection(self):
        image, _, collection, entity = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        collection.name = "default"
        db.session.commit()

        tmpf = _fake_img_file(image, b"Hello default Collection!")

        ret = self.client.get(f"/v1/imagefile/{image.entityName}//{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""),
            rf"/v1/imagefile/{image.entityName}/default/{image.containerName}:{latest_tag.name}$",
        )

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()

        # singularity requests with double slash
        ret = self.client.get(f"/v1/imagefile//{image.entityName}//{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""),
            rf"/v1/imagefile//{image.entityName}/default/{image.containerName}:{latest_tag.name}$",
        )
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()  # avoid unclosed filehandle warning
        tmpf.close()

    def test_pull_default_entity_default_collection(self):
        image, _, collection, entity = _create_image()
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        collection.name = "default"
        entity.name = "default"
        db.session.commit()

        tmpf = _fake_img_file(image, b"Hello default Collection!")

        ret = self.client.get(f"/v1/imagefile///{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""), rf"/v1/imagefile//default/{image.containerName}:{latest_tag.name}$"
        )
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()

        # singularity requests with double slash
        ret = self.client.get(f"/v1/imagefile////{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""), rf"/v1/imagefile//default//{image.containerName}:{latest_tag.name}$"
        )
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(
            ret.headers.get("Location", ""),
            rf"/v1/imagefile//default/default/{image.containerName}:{latest_tag.name}$",
        )
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 308)
        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()  # avoid unclosed filehandle warning

        ret = self.client.get(f"/v1/imagefile//{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 308)
        self.assertRegex(ret.headers.get("Location", ""), rf"/v1/imagefile/{image.containerName}:{latest_tag.name}$")

        ret = self.client.get(ret.headers.get("Location"))
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()  # avoid unclosed filehandle warning

        ret = self.client.get(f"/v1/imagefile/{image.containerName}:{latest_tag.name}")
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello default Collection!")
        ret.close()  # avoid unclosed filehandle warning
        tmpf.close()

    def test_push_noauth(self):
        ret = self.client.post("/v1/imagefile/whatever")
        self.assertEqual(ret.status_code, 401)

    def test_push(self):
        image, container, _, _ = _create_image()
        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()
        image_id = image.id
        container_id = container.id

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 200)
        # no more auto-tagging
        read_image = Image.query.get(image_id)
        self.assertEqual(read_image.uploadState, UploadStates.completed)
        self.assertTrue(os.path.exists(read_image.location))
        self.assertEqual(read_image.size, os.path.getsize(read_image.location))

        db_container: Container = Container.query.get(container_id)
        self.assertDictEqual(db_container.imageTags, {"latest": str(read_image.id)}, "latest tag updated")
        self.assertDictEqual(
            db_container.archImageTags, {"amd64": {"latest": str(read_image.id)}}, "arch image tag updated"
        )
        db_image = Image.query.get(image_id)
        self.assertEqual(db_image.arch, "amd64")

    def test_check_quota(self):
        user = _create_user()
        user.quota = 1024
        image, _, _, entity = _create_image(owner=user)

        image.size = 512
        self.assertTrue(_check_quota(image))
        image.size = 2048
        self.assertFalse(_check_quota(image))

        user.quota = 0
        image.size = 2048
        self.assertTrue(_check_quota(image))

    def test_check_quota_add_size(self):
        user = _create_user()
        user.quota = 1024
        image = _create_image(owner=user)[0]

        self.assertTrue(_check_quota(image, 512))
        self.assertFalse(_check_quota(image, 1024))

    def test_check_quota_group(self):
        group = _create_group()
        group.quota = 1024
        image, _, _, entity = _create_image()
        entity.group = group

        image.size = 512
        self.assertTrue(_check_quota(image))
        image.size = 2048
        self.assertFalse(_check_quota(image))

        group.quota = 0
        self.assertTrue(_check_quota(image))

    def test_check_quota_group_user_override(self):
        """user quota beats group quota"""
        group = _create_group()
        group.quota = 4096
        user = _create_user()
        user.quota = 1024

        image, _, _, entity = _create_image(owner=user)
        entity.group = group

        image.size = 512
        self.assertTrue(_check_quota(image))

        image.size = 2048
        self.assertFalse(_check_quota(image))

        image.size = 8192
        self.assertFalse(_check_quota(image))

        # group quota exceeded, user quota not -> should fail

        group.quota = 1024
        user.quota = 4096
        image.size = 2048
        self.assertFalse(_check_quota(image))

    def test_check_quota_no_owner(self):
        image = _create_image()[0]
        image.size = 1024
        self.assertTrue(_check_quota(image))

    def test_push_quota(self):
        user = _create_user()
        image, container, _, entity = _create_image(owner=user)
        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()
        entity_id = entity.id
        user_id = user.id

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 200)
        entity = Entity.query.get(entity_id)
        self.assertEqual(entity.used_quota, len(img_data))

        user = User.query.get(user_id)
        self.assertEqual(user.used_quota, len(img_data))

    def test_push_quota_check(self):
        img_data, digest = _prepare_img_data()
        user = _create_user()
        user.quota = len(img_data) - 1
        image = _create_image(owner=user)[0]
        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        image.hash = digest
        db.session.commit()
        image_id = image.id

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 413)
        image = Image.query.get(image_id)
        self.assertEqual(image.uploadState, UploadStates.failed)

    def test_push_readonly(self):
        image, container, _, _ = _create_image()
        container.readOnly = True
        db.session.commit()

        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 406)

    def test_push_invalid_hash(self):
        image = _create_image()[0]
        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()

        img_data = b"Hello Dorian!"

        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 422)

    def test_push_create_dir(self):
        image = _create_image()[0]
        self.app.config["IMAGE_PATH"] = os.path.join(tempfile.mkdtemp(), "oink", "oink")
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 200)

    def test_push_overwrite(self):
        image = _create_image()[0]
        self.app.config["IMAGE_PATH"] = os.path.join(tempfile.mkdtemp(), "oink", "oink")
        image.uploadState = UploadStates.completed
        image.location = "/gru/nz"

        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()
        image_id = image.id
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 200)
        read_image = Image.query.get(image_id)
        self.assertNotEqual(read_image.location, "/gru/nz")

    def test_push_user(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.user
        db.session.commit()

        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 200)

    def test_push_user_other(self):
        image, container, coll, entity = _create_image()
        entity.owner = self.user
        coll.owner = self.user
        container.owner = self.other_user
        db.session.commit()

        self.app.config["IMAGE_PATH"] = tempfile.mkdtemp()
        img_data, digest = _prepare_img_data()
        image.hash = digest
        db.session.commit()

        with self.fake_auth():
            ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
        self.assertEqual(ret.status_code, 403)
