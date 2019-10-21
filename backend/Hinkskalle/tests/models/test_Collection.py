import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, CollectionSchema

def _create_collection(name='test-collection'):
  try:
    entity = Entity.objects.get(name='test-hase')
  except:
    entity = Entity(name='test-hase')
    entity.save()

  coll = Collection(name=name, entity_ref=entity)
  coll.save()
  return coll, entity


class TestCollection(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()
  
  def tearDown(self):
    Entity.objects.delete()
    Collection.objects.delete()

  def test_collection(self):
    coll, entity = _create_collection()

    read_coll = Collection.objects.get(name='test-collection')
    self.assertEqual(read_coll.id, coll.id)
    self.assertTrue(abs(read_coll.createdAt - datetime.utcnow()) < timedelta(seconds=1))

    self.assertEqual(read_coll.entity(), entity.id)
    self.assertEqual(read_coll.entityName(), entity.name)

  def test_schema(self):
    schema = CollectionSchema()
    coll, entity = _create_collection()

    serialized = schema.dump(coll)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['id'], str(coll.id))
    self.assertEqual(serialized.data['name'], coll.name)

    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)

