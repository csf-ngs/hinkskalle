import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, EntitySchema

class TestEntity(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()

  def tearDown(self):
    Entity.objects.delete()
  
  def test_entity(self):
    entity = Entity(name='test-hase')
    entity.save()

    read_entity = Entity.objects.get(name='test-hase')
    self.assertEqual(read_entity.id, entity.id)
    self.assertTrue(abs(read_entity.createdAt - datetime.utcnow()) < timedelta(seconds=1))


  def test_schema(self):
    entity = Entity(name='Test Hase')
    schema = EntitySchema()
    serialized = schema.dump(entity)
    self.assertEqual(serialized.data['id'], entity.id)
    self.assertEqual(serialized.data['name'], entity.name)

