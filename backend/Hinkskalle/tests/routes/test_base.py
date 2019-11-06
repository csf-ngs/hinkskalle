import unittest

from Hinkskalle.tests.route_base import RouteBase, fake_auth
from Hinkskalle.tests.models.test_Image import _create_image

class TestBase(RouteBase):
  def test_version(self):
    ret = self.client.get('/version')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    self.assertIn("apiVersion", json)
    self.assertIn("version", json)
  
  def test_config(self):
    ret = self.client.get('/assets/config/config.prod.json')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    self.assertDictEqual(json, {
      'keystoreAPI': { 'uri': 'http://localhost'},
      'libraryAPI': { 'uri': 'http://localhost'},
      'tokenAPI': { 'uri': 'http://localhost'},
    })

    self.app.config['PREFERRED_URL_SCHEME']='https'
    ret = self.app.test_client().get('/assets/config/config.prod.json')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    self.assertDictEqual(json, {
      'keystoreAPI': { 'uri': 'https://localhost'},
      'libraryAPI': { 'uri': 'https://localhost'},
      'tokenAPI': { 'uri': 'https://localhost'},
    })

  def test_latest(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('v1.0', image1.id)

    with fake_auth(self.app):
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertListEqual([ c['id'] for c in json ], [ str(image1.id), ] )

    images=[]
    for idx in range(1, 12):
      img, cont, _, _ = _create_image(postfix=str(idx))
      cont.tag_image('oink', img.id)
      images.append(img)
    images.reverse()
    
    with fake_auth(self.app):
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertListEqual([ c['id'] for c in json ], [ str(img.id) for img in images[:10] ] )




