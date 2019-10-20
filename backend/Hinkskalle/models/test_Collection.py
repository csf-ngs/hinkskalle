import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, CollectionSchema

class TestCollection(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()
  
  def test_collection(self):
    coll = Collection(id='test-collection', name='Test Collection')
    coll.save()

    read_coll = Collection.objects.get(id='test-collection')
    self.assertEqual(read_coll.id, coll.id)
    self.assertTrue(abs(read_coll.createdAt - datetime.utcnow()) < timedelta(seconds=1))
  
  def test_entity_ref(self):
    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    coll = Collection(id='test-collection', name='Test Collection', entity_ref=entity)
    coll.save()

    self.assertEqual(coll.entity(), entity.id)
    self.assertEqual(coll.entityName(), entity.name)

  def test_schema(self):
    coll = Collection(id='test-collection', name='Test Collection')
    schema = CollectionSchema()
    serialized = schema.dump(coll)
    self.assertEqual(serialized.data['id'], coll.id)
    self.assertEqual(serialized.data['name'], coll.name)

    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()
    coll.entity_ref=entity
    serialized = schema.dump(coll)
    self.assertEqual(serialized.data['entity'], entity.id)
    self.assertEqual(serialized.data['entityName'], entity.name)

