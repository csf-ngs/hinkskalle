from datetime import datetime, timedelta

from Hinkskalle.tests.model_base import ModelBase, _create_user
from Hinkskalle.models import Entity, EntitySchema, Collection
from Hinkskalle import db

class TestEntity(ModelBase):

  def test_entity(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()

    read_entity = Entity.query.filter_by(name='test-hase').first()
    self.assertEqual(read_entity.id, entity.id)
    self.assertTrue(abs(read_entity.createdAt - datetime.now()) < timedelta(seconds=1))
  
  def test_entity_case(self):
    entity = Entity(name='TestHase')
    db.session.add(entity)
    db.session.commit()

    read_entity = Entity.query.get(entity.id)
    self.assertEqual(read_entity.name, 'testhase')
  
  def test_count(self):
    ent = Entity(name='test-hase')
    self.assertEqual(ent.size(), 0)
    db.session.add(ent)
    db.session.commit()
    self.assertEqual(ent.size(), 0)

    coll1 = Collection(name='coll_i', entity_ref=ent)
    db.session.add(coll1)
    db.session.commit()
    self.assertEqual(ent.size(), 1)

    other_ent = Entity(name='other-hase')
    db.session.add(other_ent)
    db.session.commit()
    other_coll = Collection(name="coll_other", entity_ref=other_ent)
    db.session.add(other_coll)
    db.session.commit()

    self.assertEqual(ent.size(), 1)

  def test_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)
    entity = Entity(name='test-hase')
    self.assertTrue(entity.check_access(admin))
    self.assertFalse(entity.check_access(user))
    entity.owner=user
    self.assertTrue(entity.check_access(user))

    default = Entity(name='default')
    self.assertTrue(default.check_access(user))

  def test_update_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)
    entity = Entity(name='test-hase')

    self.assertTrue(entity.check_update_access(admin))
    self.assertFalse(entity.check_update_access(user))

    entity.owner=user
    self.assertTrue(entity.check_update_access(user))

    default = Entity(name='default')
    self.assertFalse(default.check_update_access(user))



  def test_schema(self):
    entity = Entity(name='Test Hase')
    schema = EntitySchema()
    serialized = schema.dump(entity)
    self.assertEqual(serialized.data['id'], entity.id)
    self.assertEqual(serialized.data['name'], entity.name)

    self.assertIsNone(serialized.data['deletedAt'])
    self.assertFalse(serialized.data['deleted'])

