import unittest

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



