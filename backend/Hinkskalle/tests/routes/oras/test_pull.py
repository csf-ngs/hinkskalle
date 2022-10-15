from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests._util import _fake_img_file, _create_image

from Hinkskalle import db
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Manifest import Manifest
from Hinkskalle.models.Image import Image

from datetime import datetime, timedelta


class TestOrasPull(RouteBase):
    def test_manifest(self):
        image = _create_image()[0]
        image_id = image.id
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)
        digest = ret.headers.get("Docker-Content-Digest")
        self.assertIsNotNone(digest)

        manifest = Manifest.query.filter(Manifest.hash == digest.replace("sha256:", "")).first()
        image = Image.query.get(image_id)
        self.assertIsNotNone(manifest)
        self.assertDictEqual(
            ret.get_json().get("layers")[0],
            {
                "mediaType": "application/vnd.sylabs.sif.layer.v1.sif",
                "digest": f"sha256:{image.hash.replace('sha256.', '')}",
                "size": None,
                "annotations": {
                    "org.opencontainers.image.title": image.containerName,
                },
            },
        )

    def test_manifest_stale(self):
        image = _create_image()[0]
        image_id = image.id
        tag = Tag(name="v1", image_ref=image)
        db.session.add(tag)
        image.generate_manifest()

        image.hash = "sha256.grunzgrunz"
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/v1")
        self.assertEqual(ret.status_code, 200)
        manifest = ret.get_json()
        image = Image.query.get(image_id)
        self.assertEqual(manifest.get("layers")[0].get("digest"), image.hash.replace("sha256.", "sha256:"))

    def test_manifest_noauth(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        ret = self.client.get(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest")
        self.assertEqual(ret.status_code, 401)

    def test_manifest_user(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.owner = self.user
        collection.owner = self.user
        entity.owner = self.user

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)

    def test_manifest_user_other(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.owner = self.other_user
        collection.owner = self.other_user
        entity.owner = self.other_user

        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)

    def test_manifest_private(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.private = True
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 403)

        image, container, collection, entity = _create_image(postfix="2")
        collection.private = True
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 403)

    def test_manifest_private_auth(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.private = True
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_admin_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)

    def test_manifest_private_auth_user(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.owner = self.user
        collection.owner = self.user
        entity.owner = self.user
        container.private = True
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)

    def test_manifest_private_auth_user_denied(self):
        image, container, collection, entity = _create_image(postfix="1")
        container.owner = self.other_user
        collection.owner = self.other_user
        entity.owner = self.other_user
        container.private = True
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 403)

    def test_manifest_tag_not_found(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/earliest"
            )
        self.assertEqual(ret.status_code, 404)

    def test_manifest_default_not_found(self):
        image, container, collection, entity = _create_image(postfix="1")
        image_id = image.id
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        with self.fake_auth():
            ret = self.client.get(f"/v2/{image.collectionName}/{image.containerName}/manifests/latest")
        self.assertEqual(ret.status_code, 404)

    def test_manifest_default(self):
        image, container, collection, entity = _create_image(postfix="1")
        latest_tag = Tag(name="latest", image_ref=image)
        entity.name = "default"
        db.session.add(latest_tag)
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(f"/v2/{image.collectionName}/{image.containerName}/manifests/latest")
        self.assertEqual(ret.status_code, 200)

    def test_manifest_default_collection_not_found(self):
        image, container, collection, entity = _create_image(postfix="1")
        latest_tag = Tag(name="latest", image_ref=image)
        entity.name = "default"
        db.session.add(latest_tag)
        db.session.commit()
        with self.fake_auth():
            ret = self.client.get(f"/v2/{image.containerName}/manifests/latest")
        self.assertEqual(ret.status_code, 404)

    def test_manifest_default_collection(self):
        image, container, collection, entity = _create_image(postfix="1")
        latest_tag = Tag(name="latest", image_ref=image)
        entity.name = "default"
        db.session.add(latest_tag)
        collection.name = "default"
        db.session.commit()
        with self.fake_auth():
            ret = self.client.get(f"/v2/{image.containerName}/manifests/latest")
        self.assertEqual(ret.status_code, 200)

    def test_manifest_double(self):
        image = _create_image()[0]
        image_id = image.id
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)
        digest = ret.headers.get("Docker-Content-Digest")
        self.assertIsNotNone(digest)

        image = Image.query.get(image_id)
        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)
        next_digest = ret.headers.get("Docker-Content-Digest")
        self.assertEqual(digest, next_digest)

    def test_manifest_double_different_tag(self):
        image = _create_image()[0]
        image_id = image.id
        latest_tag = Tag(name="latest", image_ref=image)
        other_tag = Tag(name="other", image_ref=image)
        db.session.add(latest_tag)
        db.session.add(other_tag)

        db.session.commit()

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/latest"
            )
        self.assertEqual(ret.status_code, 200)
        digest = ret.headers.get("Docker-Content-Digest")
        self.assertIsNotNone(digest)

        image = Image.query.get(image_id)
        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/other"
            )
        self.assertEqual(ret.status_code, 200)
        next_digest = ret.headers.get("Docker-Content-Digest")
        self.assertEqual(digest, next_digest)

    def test_manifest_refetch(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
        latest_tag.manifest_ref = manifest
        db.session.commit()
        manifest_id = manifest.id

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/sha256:{manifest.hash}"
            )
        self.assertEqual(ret.status_code, 200)

        self.assertDictEqual(ret.get_json(), {"oi": "nk"})
        manifest = Manifest.query.get(manifest_id)
        self.assertEqual(manifest.downloadCount, 1)
        self.assertAlmostEqual(manifest.latestDownload, datetime.now(), delta=timedelta(seconds=2))

    def test_manifest_refetch_head(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
        latest_tag.manifest_ref = manifest
        db.session.commit()
        manifest_id = manifest.id

        with self.fake_auth():
            ret = self.client.head(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/sha256:{manifest.hash}"
            )
        self.assertEqual(ret.status_code, 200)

        manifest = Manifest.query.get(manifest_id)
        self.assertEqual(manifest.downloadCount, 0)
        self.assertIsNone(manifest.latestDownload)

    def test_manifest_hash_notfound(self):
        image = _create_image()[0]
        latest_tag = Tag(name="latest", image_ref=image)
        db.session.add(latest_tag)

        manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
        latest_tag.manifest_ref = manifest

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/sha256:{manifest.hash}oink"
            )
        self.assertEqual(ret.status_code, 404)

    def test_blob(self):
        image = _create_image()[0]
        image_id = image.id
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.data, b"Hello Dorian!")
        image = Image.query.get(image_id)
        self.assertEqual(image.downloadCount, 1)
        self.assertEqual(image.container_ref.downloadCount, 1)
        self.assertAlmostEqual(image.latestDownload, datetime.now(), delta=timedelta(seconds=2))
        self.assertAlmostEqual(image.container_ref.latestDownload, datetime.now(), delta=timedelta(seconds=2))

    def test_blob_head_no_increment(self):
        image = _create_image()[0]
        image_id = image.id
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.head(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 200)
        image = Image.query.get(image_id)
        self.assertEqual(image.downloadCount, 0)
        self.assertEqual(image.container_ref.downloadCount, 0)
        self.assertIsNone(image.latestDownload)
        self.assertIsNone(image.container_ref.latestDownload)

    def test_blob_not_uploaded(self):
        image = _create_image()[0]
        image_id = image.id

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 404)

    def test_blob_noauth(self):
        image = _create_image()[0]
        file = _fake_img_file(image)

        ret = self.client.get(
            f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
        )
        self.assertEqual(ret.status_code, 401)

    def test_blob_private(self):
        image, container, collection, entity = _create_image()
        container.private = True
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 403)

        with self.fake_admin_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 200)

    def test_blob_private_auth(self):
        image, container, collection, entity = _create_image()
        container.owner = self.user
        collection.owner = self.user
        entity.owner = self.user
        container.private = True
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 200)

    def test_blob_private_auth_user_denied(self):
        image, container, collection, entity = _create_image()
        container.owner = self.other_user
        collection.owner = self.other_user
        entity.owner = self.other_user
        container.private = True
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 403)

    def test_blob_private_auth_user_other(self):
        image, container, collection, entity = _create_image()
        container.owner = self.other_user
        collection.owner = self.other_user
        entity.owner = self.other_user
        container.private = False
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 200)

    def test_blob_unsupported(self):
        image = _create_image()[0]
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha512:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 400)

    def test_blob_not_found(self):
        image = _create_image()[0]
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}oink/{image.collectionName}/{image.containerName}/blobs/sha256:{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 404)

    def test_blob_hash_not_found(self):
        image = _create_image()[0]
        file = _fake_img_file(image)

        with self.fake_auth():
            ret = self.client.get(
                f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/sha256:oink{image.hash.replace('sha256.', '')}"
            )
        self.assertEqual(ret.status_code, 404)
