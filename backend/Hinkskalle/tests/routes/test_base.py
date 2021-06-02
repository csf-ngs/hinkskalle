import unittest
import tempfile
import os.path

from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.models import Image
from Hinkskalle import db

class TestBase(RouteBase):

  def _fake_index(self):
    tmpdir = tempfile.TemporaryDirectory()
    self.app.config['FRONTEND_PATH']=tmpdir.name
    with open(os.path.join(tmpdir.name, 'index.html'), 'w') as index_fh:
      index_fh.write(f"<title>hinkskalle</title>\n")
    return tmpdir

  def test_index(self):
    tmpdir = self._fake_index()
    ret = self.client.get('/')
    self.assertEqual(ret.status_code, 200)
    self.assertRegex(ret.data.decode('utf-8'), r'<title>hinkskalle</title>')
  
  def test_route_frontend(self):
    tmpdir = self._fake_index()
    for test_route in ['/users', '/account', '/non/existent']:
      ret = self.client.get(test_route)
      self.assertEqual(ret.status_code, 200, f"routing to {test_route}")
      self.assertRegex(ret.data.decode('utf-8'), r'<title>hinkskalle</title>')
    
    ret = self.client.get('/v1/gru/nz')
    self.assertEqual(ret.status_code, 404, f"routing to something nonexistent under api")

    with open(os.path.join(tmpdir.name, 'grunz.txt'), 'w') as grunz_fh:
      grunz_fh.write("grunz\n")
    ret = self.client.get('/grunz.txt')
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data.decode('utf-8'), 'grunz\n', 'route to existing file')

    

  def test_version(self):
    ret = self.client.get('/version')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIn("apiVersion", json)
    self.assertIn("version", json)
  
  def test_config(self):
    self.app.config['KEYSERVER_URL']='http://key.serv.er'
    ret = self.client.get('/assets/config/config.prod.json')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    self.assertDictEqual(json, {
      'keystoreAPI': { 'uri': 'http://key.serv.er'},
      'libraryAPI': { 'uri': 'http://localhost'},
      'tokenAPI': { 'uri': 'http://localhost'},
    })

    old_setting = self.app.config['PREFERRED_URL_SCHEME']
    self.app.config['PREFERRED_URL_SCHEME']='https'
    ret = self.app.test_client().get('/assets/config/config.prod.json')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    self.assertDictEqual(json, {
      'keystoreAPI': { 'uri': 'http://key.serv.er'},
      'libraryAPI': { 'uri': 'https://localhost'},
      'tokenAPI': { 'uri': 'https://localhost'},
    })
    self.app.config['PREFERRED_URL_SCHEME']=old_setting

  def test_latest(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('v1.0', image1.id)

    with self.fake_auth():
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
    
    with self.fake_admin_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertListEqual([ c['container']['id'] for c in json ], [ str(img.container_ref.id) for img in images[:10] ] )
  
  def test_latest_collect_images(self):
    image1, container1, _, _ = _create_image(postfix='hase1')
    image2 = Image(container_ref=container1, hash='blahase1')
    db.session.add(image2)
    db.session.commit()

    image3, container3, _, _ = _create_image(postfix="fuchs1")

    container1.tag_image('v1.0', image1.id)
    container1.tag_image('v2.0', image2.id)
    container3.tag_image('nomnom', image3.id)

    with self.fake_admin_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertCountEqual([ c['container']['id'] for c in json ], [ str(container.id) for container in [container1, container3]])


  def test_latest_collect_tags(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('v1.0', image1.id)
    container1.tag_image('oink', image1.id)

    with self.fake_admin_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json[0]['tags'], [ 'v1.0', 'oink'])

  def test_latest_user(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('oink', image1.id)

    with self.fake_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json[0]['tags'], [ 'oink' ])

  def test_latest_private(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('oink', image1.id)
    container1.private=True
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json, [])

  def test_latest_own_private(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('oink', image1.id)
    container1.private=True
    container1.owner = self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json[0]['tags'], [ 'oink' ])

  def test_latest_admin_private(self):
    image1, container1, _, _ = _create_image()
    container1.tag_image('oink', image1.id)
    container1.private=True
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get('/v1/latest')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertCountEqual(json[0]['tags'], [ 'oink' ])