
import unittest
import os
import json
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth
from Hinkskalle.models import Entity
from Hinkskalle.tests.models.test_Collection import _create_collection

class TestCollections(RouteBase):
  
  def test_get(self):
    coll, entity = _create_collection()

    ret = self.client.get(f"/v1/collections/{coll.entityName()}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_default(self):
    coll, entity = _create_collection()
    entity.name=''
    entity.save()

    ret = self.client.get(f"/v1/collections//{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))

  def test_create(self):
    entity = Entity(name='test-hase')
    entity.save()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['entity'], str(entity.id))
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_not_unique(self):
    coll, entity = _create_collection()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': coll.name,
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_entity(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': 'oink oink',
      })
    self.assertEqual(ret.status_code, 500)
