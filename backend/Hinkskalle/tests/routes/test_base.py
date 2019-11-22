import unittest

from Hinkskalle.tests.route_base import RouteBase, fake_auth
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.models import Image

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

    self.assertListEqual([ c['container']['id'] for c in json ], [ str(image1.container_ref.id), ] )

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

    self.assertListEqual([ c['container']['id'] for c in json ], [ str(img.container_ref.id) for img in images[:10] ] )
  
  def test_latest_collect_images(self):
    image1, container1, _, _ = _create_image(postfix='hase1')
    image2 = Image(container_ref=container1, hash='blahase1')
    image2.save()

    image3, container3, _, _ = _create_image(postfix="fuchs1")

    container1.tag_image('v1.0', image1.id)
    container1.tag_image('v2.0', image2.id)
    container3.tag_image('nomnom', image3.id)

    with fake_auth(self.app):
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertCountEqual([ c['container']['id'] for c in json ], [ str(container.id) for container in [container1, container3]])


  def test_latest_collect_tags(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('v1.0', image1.id)
    container1.tag_image('oink', image1.id)

    with fake_auth(self.app):
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json[0]['tags'], [ 'v1.0', 'oink'])

