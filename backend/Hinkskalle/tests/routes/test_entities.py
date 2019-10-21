import unittest
import os
import json
from Hinkskalle import create_app

from Hinkskalle.models import Entity

class TestEntities(unittest.TestCase):
  app = None
  client = None
  @classmethod
  def setUpClass(cls):
    os.environ['MONGODB_HOST']='mongomock://localhost'
  
  def setUp(self):
    self.app = create_app()
    self.client = self.app.test_client()

  def test_get(self):
    entity = Entity(name='grunz')
    entity.save()
    ret = self.client.get('/v1/entities/grunz')
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
  
  def __test_create(self):
    # figure out mock token
    ret = self.client.post('/v1/entities', json={
      'name': 'grunz',
    })
    data = ret.get_json().get('data')
    self.assertEquals(data['name'], 'grunz')