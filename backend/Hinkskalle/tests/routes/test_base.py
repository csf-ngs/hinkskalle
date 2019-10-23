import unittest

from Hinkskalle.tests.route_base import RouteBase

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


