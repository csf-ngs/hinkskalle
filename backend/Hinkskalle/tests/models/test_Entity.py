import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, EntitySchema, Collection
from Hinkskalle.fsk_api import FskUser

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
  
  def test_count(self):
    ent = Entity(name='test-hase')
    self.assertEqual(ent.size(), 0)
    ent.save()
    self.assertEqual(ent.size(), 0)

    coll1 = Collection(name='coll_i', entity_ref=ent)
    coll1.save()
    self.assertEqual(ent.size(), 1)

    other_ent = Entity(name='other-hase')
    other_ent.save()
    other_coll = Collection(name="coll_other", entity_ref=other_ent)
    other_coll.save()

    self.assertEqual(ent.size(), 1)

  def test_access(self):
    admin = FskUser('oink', True)
    user = FskUser('oink', False)
    entity = Entity(name='test-hase')
    self.assertTrue(entity.check_access(admin))
    self.assertFalse(entity.check_access(user))
    entity.createdBy='oink'
    self.assertTrue(entity.check_access(user))

    default = Entity(name='default')
    self.assertTrue(default.check_access(user))

  def test_update_access(self):
    admin = FskUser('oink', True)
    user = FskUser('oink', False)
    entity = Entity(name='test-hase')

    self.assertTrue(entity.check_update_access(admin))
    self.assertFalse(entity.check_update_access(user))

    entity.createdBy='oink'
    self.assertTrue(entity.check_update_access(user))

    default = Entity(name='default')
    self.assertFalse(default.check_update_access(user))



  def test_schema(self):
    entity = Entity(name='Test Hase')
    schema = EntitySchema()
    serialized = schema.dump(entity)
    self.assertEqual(serialized.data['id'], entity.id)
    self.assertEqual(serialized.data['name'], entity.name)

