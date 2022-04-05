from datetime import datetime, timedelta

from Hinkskalle.models.Entity import Entity, EntitySchema
from Hinkskalle.models.Collection import Collection
from Hinkskalle import db
from Hinkskalle.models.Image import UploadStates
from ..model_base import ModelBase
from .._util import _create_user, _create_image

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
    self.assertEqual(ent.size, 0)
    db.session.add(ent)
    db.session.commit()
    self.assertEqual(ent.size, 0)

    coll1 = Collection(name='coll_i', entity_ref=ent)
    db.session.add(coll1)
    db.session.commit()
    self.assertEqual(ent.size, 1)

    other_ent = Entity(name='other-hase')
    db.session.add(other_ent)
    db.session.commit()
    other_coll = Collection(name="coll_other", entity_ref=other_ent)
    db.session.add(other_coll)
    db.session.commit()

    self.assertEqual(ent.size, 1)

  def test_used_quota_null(self):
    ent = Entity(name='test-quota')
    self.assertEqual(ent.calculate_used(), 0)
    self.assertEqual(ent.used_quota, 0)

    image1 = _create_image(postfix='1')[0]
    image1.container_ref.collection_ref.entity_ref=ent
    image1.size = None
    image1.uploadState = UploadStates.completed
    self.assertEqual(ent.calculate_used(), 0)
  
  def test_used_quota(self):
    ent = Entity(name='test-quota')
    self.assertEqual(ent.calculate_used(), 0)
    self.assertEqual(ent.used_quota, 0)

    image1 = _create_image(postfix='1')[0]
    image1.container_ref.collection_ref.entity_ref=ent
    image1.size=200
    image1.location='/da/ham1'
    image1.uploadState=UploadStates.completed
    
    self.assertEqual(ent.calculate_used(), 200)
    self.assertEqual(ent.used_quota, 200)
    self.assertEqual(image1.container_ref.used_quota, 200)
    self.assertEqual(image1.container_ref.collection_ref.used_quota, 200)

    image2 = _create_image(postfix='2')[0]
    image2.container_ref.collection_ref.entity_ref=ent
    image2.size=300
    image2.location='/da/ham2'
    image2.uploadState=UploadStates.completed

    self.assertEqual(ent.calculate_used(), 500)
    self.assertEqual(image2.container_ref.used_quota, 300)
    self.assertEqual(image2.container_ref.collection_ref.used_quota, 300)

    image2_same = _create_image(postfix='2_same')[0]
    image2_same.container_ref.collection_ref.entity_ref=ent
    image2_same.size=400
    image2_same.location='/da/ham2'
    image2_same.uploadState=UploadStates.completed

    self.assertEqual(ent.calculate_used(), 500)
    self.assertEqual(image2_same.container_ref.used_quota, 400)
    self.assertEqual(image2_same.container_ref.collection_ref.used_quota, 400)

    image3 = _create_image(postfix='3')[0]
    image3.container_ref.collection_ref=image2_same.container_ref.collection_ref
    image3.size=600
    image3.location='/da/ham2'
    image3.uploadState=UploadStates.completed

    self.assertEqual(ent.calculate_used(), 500)
    self.assertEqual(image3.container_ref.used_quota, 600)
    self.assertEqual(image3.container_ref.collection_ref.used_quota, 400)


    image4_upl = _create_image(postfix='4')[0]
    image4_upl.container_ref.collection_ref.entity_ref=ent
    image4_upl.size=300
    image4_upl.location='/da/ham3'
    image4_upl.uploadState=UploadStates.broken

    self.assertEqual(ent.calculate_used(), 500)
    self.assertEqual(image4_upl.container_ref.used_quota, 0)
    self.assertEqual(image4_upl.container_ref.collection_ref.used_quota, 0)

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
    self.assertEqual(serialized['id'], entity.id)
    self.assertEqual(serialized['name'], entity.name)

    self.assertIsNone(serialized['deletedAt'])
    self.assertFalse(serialized['deleted'])

    entity.used_quota = 999
    serialized = schema.dump(entity)
    self.assertEqual(serialized['usedQuota'], 999)


  def test_quota_default(self):
    entity = Entity(name='test1hase')
    db.session.add(entity)
    db.session.commit()
    self.assertEqual(entity.quota, 0)

    self.app.config['DEFAULT_USER_QUOTA']=100
    entity = Entity(name='test2hase')
    db.session.add(entity)
    db.session.commit()
    self.assertEqual(entity.quota, 100)
    self.app.config.pop('DEFAULT_USER_QUOTA')