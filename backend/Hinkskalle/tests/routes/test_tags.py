import unittest
import os.path
import os
from tempfile import mkdtemp

from Hinkskalle.models import Container
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth
from Hinkskalle.tests.models.test_Image import _create_image


class TestTags(RouteBase):
  def test_get(self):
    image, container, _, _ = _create_image()
    ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {})

    container.tag_image('v1.0', image.id)
    ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'v1.0': str(image.id)})

    container.tag_image('oink', image.id)
    ret = self.client.get(f"/v1/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'v1.0': str(image.id), 'oink': str(image.id)})

  def test_update(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': str(image.id)})
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, { 'v1.0': str(image.id) })
    self.assertDictEqual(container.imageTags(), { 'v1.0': str(image.id) })

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'oink': str(image.id)})
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertDictEqual(data, { 'v1.0': str(image.id), 'oink': str(image.id) })
    self.assertDictEqual(container.imageTags(), { 'v1.0': str(image.id), 'oink': str(image.id) })
  
  def test_symlinks(self):
    image, container, _, _ = _create_image()
    self._fake_uploaded_image(image)

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': str(image.id)})
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
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': str(image.id)})
    self.assertEqual(ret.status_code, 200)
    self.assertTrue(os.path.exists(link_location))
    self.assertTrue(os.path.samefile(link_location, image.location))

    os.remove(link_location)
    # overwrite dangling links, too
    os.symlink('/oink/oink/gru.nz', link_location)
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': str(image.id)})
    self.assertEqual(ret.status_code, 200)

  def test_symlinks_default_entity(self):
    image, container, _, entity = _create_image()
    self._fake_uploaded_image(image)
    entity.name='default'
    entity.save()

    link_location = os.path.join(self.app.config['IMAGE_PATH'], image.collectionName(), f"{image.containerName()}_v1.0.sif")
    
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': str(image.id)})
    self.assertEqual(ret.status_code, 200)
    self.assertTrue(os.path.exists(link_location))
    self.assertTrue(os.path.samefile(link_location, image.location))

  def test_update_old(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={ 'Tag': 'v1', 'ImageID': str(image.id) })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertDictEqual(data, { 'v1': str(image.id) })

  
  def test_update_invalid(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': 'oink'})
    self.assertEqual(ret.status_code, 404)
    invalidid = str(image.id)[::-1]

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/tags/{container.id}", json={'v1.0': invalidid})
    self.assertEqual(ret.status_code, 404)

  def _fake_uploaded_image(self, image):
    self.app.config['IMAGE_PATH']=mkdtemp()
    img_base = os.path.join(self.app.config['IMAGE_PATH'], '_imgs')
    os.makedirs(img_base, exist_ok=True)
    image.uploaded = True
    image.location = os.path.join(img_base, 'testhase.sif')
    image.save()
    with open(image.location, 'w') as outfh:
      outfh.write('I am Testhase!')



