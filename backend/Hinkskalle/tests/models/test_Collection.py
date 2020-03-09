from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, CollectionSchema, Container
from Hinkskalle.fsk_api import FskUser

from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase

def _create_collection(name='test-collection'):
  try:
    entity = Entity.query.filter_by(name='test-hase').one()
  except:
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()


  coll = Collection(name=name, entity_id=entity.id)
  db.session.add(coll)
  db.session.commit()
  return coll, entity


class TestCollection(ModelBase):
  def test_collection(self):
    coll, entity = _create_collection()

    read_coll = Collection.query.filter_by(name='test-collection').one()
    self.assertEqual(read_coll.id, coll.id)
    self.assertTrue(abs(read_coll.createdAt - datetime.utcnow()) < timedelta(seconds=1))

    self.assertEqual(read_coll.entity(), entity.id)
    self.assertEqual(read_coll.entityName(), entity.name)
  
  def test_count(self):
    coll, entity = _create_collection()
    self.assertEqual(coll.size(), 0)
    no_create = Collection(name='no-create', entity_ref=entity)
    self.assertEqual(no_create.size(), 0)

    cont1 = Container(name='cont_i', collection_ref=coll)
    db.session.add(cont1)
    db.session.commit()
    self.assertEqual(coll.size(), 1)

    other_coll, _ = _create_collection('other')
    other_cont = Container(name='cont_other', collection_ref=other_coll)
    db.session.add(other_cont)
    db.session.commit()

    self.assertEqual(coll.size(), 1)

  
  def test_access(self):
    admin = FskUser('oink', True)
    user = FskUser('oink', False)
    coll, entity = _create_collection('other')
    self.assertTrue(coll.check_access(admin))
    self.assertFalse(coll.check_access(user))

    coll, entity = _create_collection('own')
    entity.createdBy='oink'
    db.session.commit()
    coll.createdBy='oink'
    self.assertTrue(coll.check_access(user))
    coll.createdBy='muh'
    self.assertFalse(coll.check_access(user))

    coll, entity = _create_collection('own-default')
    entity.createdBy='muh'
    db.session.commit()
    coll.createdBy='oink'
    self.assertTrue(coll.check_access(user))

    coll, default = _create_collection('default')
    default.name='default'
    db.session.commit()
    coll.createdBy='oink'
    self.assertTrue(coll.check_access(user))
    coll.createdBy='muh'
    self.assertFalse(coll.check_access(user))
  
  def test_update_access(self):
    admin = FskUser('admin.oink', True)
    user = FskUser('user.oink', False)

    coll, _ = _create_collection('other')
    self.assertTrue(coll.check_update_access(admin))
    self.assertFalse(coll.check_update_access(user))

    coll, _ = _create_collection('own')
    coll.createdBy = user.username 
    self.assertTrue(coll.check_update_access(user))

    coll, default = _create_collection('default')
    default.name='default'
    db.session.commit()
    self.assertFalse(coll.check_update_access(user))

  def test_schema(self):
    schema = CollectionSchema()
    coll, entity = _create_collection()

    serialized = schema.dump(coll)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['id'], str(coll.id))
    self.assertEqual(serialized.data['name'], coll.name)

    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)

    self.assertIsNone(serialized.data['deletedAt'])
    self.assertFalse(serialized.data['deleted'])

