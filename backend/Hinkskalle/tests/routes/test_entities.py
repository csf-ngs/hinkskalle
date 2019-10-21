import unittest
import os
import json
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth

from Hinkskalle.models import Entity

class TestEntities(RouteBase):
  def test_get(self):
    entity = Entity(name='grunz')
    entity.save()
    ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    json['data'].pop('createdAt')
    self.assertDictEqual(json['data'], {
      'id': str(entity.id),
      'name': entity.name,
      'description': entity.description,
      'customData': entity.customData,
      'quota': entity.quota,
      'size': entity.size(),
      'defaultPrivate': entity.defaultPrivate,
      #'createdAt': entity.createdAt.isoformat('T', timespec='milliseconds'),
      'createdBy': entity.createdBy,
      'updatedAt': entity.updatedAt,
      'deletedAt': entity.deletedAt,
      'deleted': entity.deleted,
    })
  
  def test_get_default(self):
    entity = Entity(name='')
    entity.save()

    ret = self.client.get('/v1/entities/')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))

  def test_create(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
        'createdAt': '0001-01-01T00:00:00Z',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'grunz')
    self.assertNotEqual(data['createdAt'], '0001-01-01T00:00:00+00:00')
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_not_unique(self):
    entity = Entity(name='grunz')
    entity.save()

    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
      })
    self.assertEqual(ret.status_code, 412)