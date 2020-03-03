import unittest
import os.path
import os
from tempfile import mkdtemp

from Hinkskalle import db
from Hinkskalle.models import Container
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth
from Hinkskalle.tests.models.test_Image import _create_image


class TestTags(RouteBase):
  def test_get_noauth(self):
    ret = self.client.get(f"/v1/tags/whatever")
    self.assertEqual(ret.status_code, 401)

  def test_get(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {})

    container.tag_image('v1.0', image.id)
    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'v1.0': image.id})

    container.tag_image('oink', image.id)
    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'v1.0': image.id, 'oink': image.id})
  
  def test_get_user(self):
    image, container, coll, entity = _create_image()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.hase'
    db.session.commit()

    container.tag_image('v1.0', image.id)
    with fake_auth(self.app):
      ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other(self):
    image, container, coll, entity = _create_image()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.kuh'
    db.session.commit()

    container.tag_image('v1.0', image.id)
    with fake_auth(self.app):
      ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 403)

  def test_update(self):
    image, container, _, _ = _create_image()
    container_id=container.id
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, { 'v1.0': image.id })
    db_container=Container.query.get(container_id)
    self.assertDictEqual(db_container.imageTags(), { 'v1.0': image.id })

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'oink': image.id})
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertDictEqual(data, { 'v1.0': image.id, 'oink': image.id })
    db_container=Container.query.get(container_id)
    self.assertDictEqual(db_container.imageTags(), { 'v1.0': image.id, 'oink': image.id })

  def test_update_user(self):
    image, container, coll, entity = _create_image()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.hase'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)

  def test_update_user_other(self):
    image, container, coll, entity = _create_image()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.kuh'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 403)
  
  def test_symlinks(self):
    image, container, _, _ = _create_image()
    self._fake_uploaded_image(image)

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)
    
    link_location = os.path.join(self.app.config['IMAGE_PATH'], image.entityName(), image.collectionName(), f"{image.containerName()}_v1.0.sif")
    self.assertTrue(os.path.exists(link_location))
    self.assertTrue(os.path.samefile(link_location, image.location))
  
  def test_symlinks_existing(self):
    image, container, _, _ = _create_image()
    self._fake_uploaded_image(image)

    link_location = os.path.join(self.app.config['IMAGE_PATH'], image.entityName(), image.collectionName(), f"{image.containerName()}_v1.0.sif")
    os.makedirs(os.path.dirname(link_location), exist_ok=True)
    with open(link_location, 'w') as outfh:
      outfh.write('muh')
    
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)
    self.assertTrue(os.path.exists(link_location))
    self.assertTrue(os.path.samefile(link_location, image.location))

    os.remove(link_location)
    # overwrite dangling links, too
    os.symlink('/oink/oink/gru.nz', link_location)
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)

  def test_symlinks_default_entity(self):
    image, container, _, entity = _create_image()
    self._fake_uploaded_image(image)
    entity.name='default'
    db.session.commit()

    link_location = os.path.join(self.app.config['IMAGE_PATH'], image.collectionName(), f"{image.containerName()}_v1.0.sif")
    
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': image.id})
    self.assertEqual(ret.status_code, 200)
    self.assertTrue(os.path.exists(link_location))
    self.assertTrue(os.path.samefile(link_location, image.location))

  def test_update_old(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={ 'Tag': 'v1', 'ImageID': image.id })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertDictEqual(data, { 'v1': image.id })

  
  def test_update_invalid(self):
    image, container, _, _ = _create_image()
    image_id=image.id
    container_id=container.id
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': 'oink'})
    self.assertEqual(ret.status_code, 404)
    invalidid = image_id*-1

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container_id}", json={'v1.0': invalidid})
    self.assertEqual(ret.status_code, 404)

  def _fake_uploaded_image(self, image):
    self.app.config['IMAGE_PATH']=mkdtemp()
    img_base = os.path.join(self.app.config['IMAGE_PATH'], '_imgs')
    os.makedirs(img_base, exist_ok=True)
    image.uploaded = True
    image.location = os.path.join(img_base, 'testhase.sif')
    db.session.commit()
    with open(image.location, 'w') as outfh:
      outfh.write('I am Testhase!')



