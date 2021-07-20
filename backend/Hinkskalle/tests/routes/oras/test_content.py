from Hinkskalle.models.Entity import Entity
import os.path

from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests._util import _fake_img_file, _create_image

from Hinkskalle import db
from Hinkskalle.models.Image import Image
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Manifest import Manifest

class TestOrasContent(RouteBase):

  def test_tag_list_noauth(self):
    image = _create_image()[0]
    tag1 = Tag(name='oink', image_ref=image)

    db.session.add(tag1)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list")
    self.assertEqual(ret.status_code, 401)

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

  def test_tag_list_user(self):
    image, container, collection, entity = _create_image()
    container.owner = self.user
    collection.owner = self.user
    entity.owner = self.user
    tag1 = Tag(name='oink', image_ref=image)

    db.session.add(tag1)

    with self.fake_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list")
    self.assertEqual(ret.status_code, 200)

  def test_tag_list_user_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='oink', image_ref=image)

    db.session.add(tag1)

    with self.fake_auth():
      ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/tags/list")
    self.assertEqual(ret.status_code, 403)

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

 
  def test_delete_tag_noauth(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2")
    self.assertEqual(ret.status_code, 401)
  
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

  def test_delete_tag_user(self):
    image, container, collection, entity = _create_image()
    container.owner = self.user
    collection.owner = self.user
    entity.owner = self.user
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2")
    self.assertEqual(ret.status_code, 202)

  def test_delete_tag_user_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2")
    self.assertEqual(ret.status_code, 403)

  def test_delete_tag_user_denied_tag(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='v2', image_ref=image, owner=self.other_user)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2")
    self.assertEqual(ret.status_code, 403)

  def test_delete_tag_not_found(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/v2oink")
    self.assertEqual(ret.status_code, 404)

  def test_delete_manifest_noauth(self):
    image = _create_image()[0]
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 401)

  def test_delete_manifest(self):
    image = _create_image()[0]
    image_id = image.id
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
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

  def test_delete_manifest_user(self):
    image, container, collection, entity = _create_image()
    container.owner = self.user
    collection.owner = self.user
    entity.owner = self.user
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}', container_ref=container)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 202)

  def test_delete_manifest_user_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}', container_ref=container)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 403)

  def test_delete_manifest_not_found(self):
    image = _create_image()[0]
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content='{"oi": "nk"}', container_ref=image.container_ref)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}oink")
    self.assertEqual(ret.status_code, 404)

  def test_delete_blob_noauth(self):
    image = _create_image()[0]
    image_id = image.id
    file = _fake_img_file(image)

    ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 401)

  def test_delete_blob(self):
    image = _create_image()[0]
    image_id = image.id
    file = _fake_img_file(image)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNone(Image.query.get(image_id))
    self.assertFalse(os.path.exists(image.location))

  def test_delete_blob_quota(self):
    image, _, _, entity = _create_image()
    _fake_img_file(image)
    image.size = 100
    entity.calculate_used()
    entity_id = entity.id
    db.session.commit()
    self.assertEqual(entity.used_quota, 100)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 202)
    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, 0)

  def test_delete_blob_user(self):
    image, container, collection, entity = _create_image()
    container.owner = self.user
    collection.owner = self.user
    entity.owner = self.user
    file = _fake_img_file(image)

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 202)

  def test_delete_blob_user_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    file = _fake_img_file(image)

    with self.fake_auth():
      ret = self.client.delete(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 403)

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