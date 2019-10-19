import unittest
from mongoengine import connect, disconnect

from Hinkskalle.models import Entity, EntitySchema

class TestEntity(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()
  
  def test_entity(self):
    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    read_entity = Entity.objects.get(id='test-hase')
    self.assertEqual(read_entity.id, entity.id)

  def test_schema(self):
    entity = Entity(id='test-hase', name='Test Hase')
    schema = EntitySchema()
    serialized = schema.dump(entity)
    self.assertEqual(serialized.data['id'], entity.id)
    self.assertEqual(serialized.data['name'], entity.name)

