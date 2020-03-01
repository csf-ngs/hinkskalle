
import unittest
import os
import json
import tempfile
import datetime
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth
from Hinkskalle.tests.models.test_Container import _create_container
from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle.models import Container
from Hinkskalle import db

class TestContainers(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/containers/what/ever')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container2.collection_ref=coll
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 2)
    self.assertListEqual([ c['name'] for c in json ], [ container1.name, container2.name ] )
  
  def test_list_user(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container1.createdBy='test.hase'
    container2.createdBy='test.hase'
    container2.collection_ref=coll
    coll.createdBy='test.hase'
    entity.createdBy='test.hase'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ container1.name, container2.name ])

  def test_list_user_default(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container1.createdBy='test.hase'
    container2.createdBy='test.kuh'
    coll.createdBy='test.hase'
    entity.name='default'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/default/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ container1.name ])
  
  def test_list_user_other(self):
    _, coll, entity = _create_container('coll1')
    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)

  def test_get_noauth(self):
    ret = self.client.get('/v1/containers/what/ev/er')
    self.assertEqual(ret.status_code, 401)

  def test_get(self):
    container, coll, entity = _create_container()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)
  
  def test_get_default_entity(self):
    container, coll, entity = _create_container()
    entity.name='default'
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers//{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/{coll.name}/{container.name}")

    with fake_admin_auth(self.app):
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)
  
  def test_get_default_collection(self):
    container, coll, entity = _create_container()
    coll.name='default'
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}//{container.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/{entity.name}/default/{container.name}$")
    with fake_admin_auth(self.app):
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)

  def test_get_default_collection_default_entity(self):
    container, coll, entity = _create_container()
    entity.name='default'
    coll.name='default'
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers///{container.name}")
    self.assertEqual(ret.status_code, 308, 'triple slash')
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default//{container.name}$")
    with fake_admin_auth(self.app):
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308, 'triple slash')
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/default/{container.name}$")

    with fake_admin_auth(self.app):
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)

    # double slash expansion gives an ambigous route (collides with list containers)
    # maybe we get by without it
    # with fake_admin_auth(self.app):
    #   ret = self.client.get(f"/v1/containers//{container.name}")
    # self.assertEqual(ret.status_code, 308, 'double slash')
    # self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/{container.name}$")

    # with fake_admin_auth(self.app):
    #   ret = self.client.get(ret.headers.get('Location'))
    # self.assertEqual(ret.status_code, 200)
    # data = ret.get_json().get('data')
    # self.assertEqual(data['id'], container.id)

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers/{container.name}")
    self.assertEqual(ret.status_code, 200, 'single slash')
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)

  def test_get_user(self):
    container, coll, entity = _create_container()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.hase'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], container.id)

  def test_get_user_other(self):
    container, coll, entity = _create_container()
    entity.createdBy='test.hase'
    coll.createdBy='test.hase'
    container.createdBy='test.kuh'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 403)

  def test_create(self):
    coll, _ = _create_collection()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': coll.id,
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['collection'], coll.id)
    self.assertEqual(data['createdBy'], 'test.hase')
  
  def test_create_private(self):
    coll, _ = _create_collection()
    coll.private = True
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': coll.id,
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    dbContainer = Container.query.get(data['id'])
    self.assertTrue(dbContainer.private)

    coll2, _ = _create_collection('no-private')
    coll2.private = False
    db.session.commit()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'auch.oink',
        'collection': coll2.id,
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    dbContainer = Container.query.get(data['id'])
    self.assertFalse(dbContainer.private)





  def test_create_not_unique(self):
    container, coll, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': container.name,
        'collection': coll.id,
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_collection(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': -666,
      })
    self.assertEqual(ret.status_code, 500)
  
  def test_create_user(self):
    coll, entity = _create_collection()
    entity.createdBy = 'test.hase'
    coll.createdBy = 'test.hase'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': coll.id,
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_other(self):
    coll, entity = _create_collection()
    entity.createdBy = 'test.hase'
    coll.createdBy = 'test.kuh'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': coll.id,
      })
    self.assertEqual(ret.status_code, 403)
  
  def test_update(self):
    container, coll, entity = _create_container()

    with fake_admin_auth(self.app):
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
        'fullDescription': 'Der hot Drei Eckn',
        'private': True,
        'readOnly': True,
        'vcsUrl': 'http://da.ham',
      })
    
    self.assertEqual(ret.status_code, 200)

    dbContainer = Container.query.filter(Container.name==container.name).one()
    self.assertEqual(dbContainer.description, 'Mei Huat')
    self.assertEqual(dbContainer.fullDescription, 'Der hot Drei Eckn')
    self.assertTrue(dbContainer.private)
    self.assertTrue(dbContainer.readOnly)
    self.assertEqual(dbContainer.vcsUrl, 'http://da.ham')

    self.assertTrue(abs(dbContainer.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
    

  def test_update_user(self):
    container, coll, entity = _create_container()
    container.createdBy = 'test.hase'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
        'fullDescription': 'Der hot Drei Eckn',
        'private': True,
        'readOnly': True,
        'vcsUrl': 'http://da.ham',
      })
    
    self.assertEqual(ret.status_code, 200)

  def test_update_user_other(self):
    container, coll, entity = _create_container()
    container.createdBy = 'test.ziege'
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
      })
    
    self.assertEqual(ret.status_code, 403)