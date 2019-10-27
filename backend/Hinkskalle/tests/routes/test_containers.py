
import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth
from Hinkskalle.tests.models.test_Container import _create_container
from Hinkskalle.tests.models.test_Collection import _create_collection

class TestContainers(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/containers/what/ever')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container2.collection_ref=coll
    container2.save()

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
    container1.save()
    container2.createdBy='test.hase'
    container2.collection_ref=coll
    container2.save()
    coll.createdBy='test.hase'
    coll.save()
    entity.createdBy='test.hase'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ container1.name, container2.name ])

  def test_list_user_default(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container1.createdBy='test.hase'
    container1.save()
    container2.createdBy='test.kuh'
    container2.save()
    coll.createdBy='test.hase'
    coll.save()
    entity.name='default'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/default/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ container1.name ])
  
  def test_list_user_other(self):
    container, coll, entity = _create_container('coll1')
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
    self.assertEqual(data['id'], str(container.id))
  
  def test_get_default(self):
    container, coll, entity = _create_container()
    entity.name='default'
    entity.save()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers//{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))

  def test_get_user(self):
    container, coll, entity = _create_container()
    entity.createdBy='test.hase'
    entity.save()
    coll.createdBy='test.hase'
    coll.save()
    container.createdBy='test.hase'
    container.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))

  def test_get_user_other(self):
    container, coll, entity = _create_container()
    entity.createdBy='test.hase'
    entity.save()
    coll.createdBy='test.hase'
    coll.save()
    container.createdBy='test.kuh'
    container.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 403)

  def test_create(self):
    coll, _ = _create_collection()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['collection'], str(coll.id))
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_not_unique(self):
    container, coll, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': container.name,
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_collection(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': 'oink oink',
      })
    self.assertEqual(ret.status_code, 500)
  
  def test_create_user(self):
    coll, entity = _create_collection()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.hase'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_other(self):
    coll, entity = _create_collection()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.kuh'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 403)