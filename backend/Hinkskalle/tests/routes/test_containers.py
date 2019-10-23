
import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth
from Hinkskalle.tests.models.test_Container import _create_container

class TestContainers(RouteBase):
  def test_get(self):
    container, coll, entity = _create_container()

    ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))
  
  def test_get_default(self):
    container, coll, entity = _create_container()
    entity.name='default'
    entity.save()

    ret = self.client.get(f"/v1/containers//{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))

  def test_create(self):
    _, coll, _ = _create_container()
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


  
