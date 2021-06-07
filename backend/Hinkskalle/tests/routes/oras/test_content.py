import os.path

from Hinkskalle.tests.route_base import RouteBase
from ..test_imagefiles import _fake_img_file
from Hinkskalle.tests.models.test_Image import _create_image

from Hinkskalle import db
from Hinkskalle.models.Image import Image
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Manifest import Manifest

class TestOrasContent(RouteBase):

  def test_tag_list(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)
    tag2 = Tag(name='grunz', image_ref=image)
    tag3 = Tag(name='007', image_ref=image)

    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(tag3)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [
        '007',
        'grunz',
        'oink',
      ]
    }, ret_data)

  def test_tag_list_limit(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)
    tag2 = Tag(name='grunz', image_ref=image)
    tag3 = Tag(name='007', image_ref=image)

    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(tag3)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?n=1")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [
        '007',
      ]
    }, ret_data)

  def test_tag_list_limit_zero(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)

    db.session.add(tag1)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?n=0")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [ ]
    }, ret_data)

  def test_tag_list_limit_more(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)

    db.session.add(tag1)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?n=3")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [ 'oink' ]
    }, ret_data)

  def test_tag_list_last(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)
    tag2 = Tag(name='grunz', image_ref=image)
    tag3 = Tag(name='007', image_ref=image)

    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(tag3)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?last=007")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [
        'grunz',
        'oink',
      ]
    }, ret_data)

  def test_tag_list_last_count(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)
    tag2 = Tag(name='grunz', image_ref=image)
    tag3 = Tag(name='007', image_ref=image)

    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(tag3)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?last=007&n=1")
    self.assertEqual(ret.status_code, 200)
    ret_data = ret.get_json()
    self.assertDictEqual({
      "name": f"{image.entityName()}/{image.collectionName()}/{image.containerName()}",
      "tags": [
        'grunz',
      ]
    }, ret_data)

  def test_tag_list_last_not_found(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)
    tag2 = Tag(name='grunz', image_ref=image)
    tag3 = Tag(name='007', image_ref=image)

    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(tag3)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list?last=muuh")
    self.assertEqual(ret.status_code, 404)

 
  
  def test_delete_tag(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNone(Tag.query.filter(Tag.name=='v2', Tag.image_id==image_id).first())

  def test_delete_tag_not_found(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2oink")
    self.assertEqual(ret.status_code, 404)

  def test_delete_manifest(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}')
    manifest_id = manifest.id
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNone(Manifest.query.get(manifest_id))
    self.assertIsNone(Tag.query.filter(Tag.name=='v2', Tag.image_id==image_id).first())

  def test_delete_manifezt_not_found(self):
    image = _create_image()[0]
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}')
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}oink")
    self.assertEqual(ret.status_code, 404)

  def test_delete_blob(self):
    image = _create_image()[0]
    image_id = image.id
    file = _fake_img_file(image)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNone(Image.query.get(image_id))
    self.assertFalse(os.path.exists(image.location))

  def test_delete_blob_other_reference(self):
    image = _create_image()[0]
    image_id = image.id
    file = _fake_img_file(image)
    other_image = _create_image(postfix='other')[0]
    other_image.location = image.location
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNone(Image.query.get(image_id))
    self.assertTrue(os.path.exists(image.location))

  def test_delete_blob_not_found(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}oink")
    self.assertEqual(ret.status_code, 404)