from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle import db
from Hinkskalle.models import Tag, Manifest
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.tests.routes.test_imagefiles import _fake_img_file

class TestOras(RouteBase):

  def test_manifest(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertIsNotNone(digest)

    manifest = Manifest.query.filter(Manifest.image_ref == image, Manifest.hash == digest.replace('sha256:', '')).first()
    self.assertIsNotNone(manifest)
    self.assertDictEqual(ret.get_json().get('layers')[0], {
      'mediaType': 'application/vnd.sylabs.sif.layer.v1.sif',
      'digest': f"sha256:{image.hash.replace('sha256.', '')}",
      'size': None,
      'annotations': {
        'org.opencontainers.image.title': image.containerName(),
      }
    })
  
  def test_manifest_tag_not_found(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/earliest")
    self.assertEqual(ret.status_code, 404)

  
  def test_manifest_default(self):
    image, container, collection, entity = _create_image(postfix='1')
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    ret = self.client.get(f"/v2/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 404)

    entity.name='default'
    db.session.commit()

    ret = self.client.get(f"/v2/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)

    ret = self.client.get(f"/v2/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 404)

    collection.name='default'
    db.session.commit()
    ret = self.client.get(f"/v2/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)



  def test_manifest_double(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertIsNotNone(digest)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    next_digest = ret.headers.get('Docker-Content-Digest')
    self.assertEqual(digest, next_digest)
  
  def test_manifest_refetch(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    manifest = Manifest(image_ref=image, content='{"oi": "nk"}')

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 200)

    self.assertDictEqual(ret.get_json(), {'oi': 'nk'})

  def test_manifest_hash_notfound(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    manifest = Manifest(image_ref=image, content='{"oi": "nk"}')

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}oink")
    self.assertEqual(ret.status_code, 404)

  def test_blob(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b'Hello Dorian!')

  def test_blob_unsupported(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha512:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 400)

  def test_blob_not_found(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}oink/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 404)

  def test_blob_hash_not_found(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:oink{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 404)