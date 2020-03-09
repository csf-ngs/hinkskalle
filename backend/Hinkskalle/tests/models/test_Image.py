import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, Container, Image, ImageSchema, Tag

from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle.fsk_api import FskUser

from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase

def _create_image(hash='sha256.oink', postfix='container'):
  try:
    coll = Collection.query.filter_by(name=f"test-coll-{postfix}").one()
    entity = coll.entity_ref
  except:
    coll, entity = _create_collection(f"test-coll-{postfix}")

  try:
    container = Container.query.filter_by(name=f"test-{postfix}").one()
  except:
    container = Container(name=f"test-{postfix}", collection_ref=coll)
    db.session.add(container)
    db.session.commit()

  image = Image(container_ref=container, hash=hash)
  db.session.add(image)
  db.session.commit()
  return image, container, coll, entity

class TestImage(ModelBase):

  def test_image(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()

    coll = Collection(name='test-collection', entity_ref=entity)
    db.session.add(coll)
    db.session.commit()

    container = Container(name='test-container',collection_ref=coll)
    db.session.add(container)
    db.session.commit()

    image = Image(description='test-image', container_ref=container)
    db.session.add(image)
    db.session.commit()

    read_image = Image.query.get(image.id)
    self.assertTrue(abs(read_image.createdAt - datetime.utcnow()) < timedelta(seconds=1))

    self.assertEqual(read_image.container(), container.id)
    self.assertEqual(read_image.containerName(), container.name)

    self.assertEqual(read_image.collection(), coll.id)
    self.assertEqual(read_image.collectionName(), coll.name)

    self.assertEqual(read_image.entity(), entity.id)
    self.assertEqual(read_image.entityName(), entity.name)

  def test_tags(self):
    image = _create_image()[0]

    tag1 = Tag(name='v1', image_ref=image)
    db.session.add(tag1)
    db.session.commit()
    tag2 = Tag(name='v2', image_ref=image)
    db.session.add(tag2)
    db.session.commit()

    self.assertListEqual(image.tags(), ['v1', 'v2'])
    Tag.__table__.delete()
  
  def test_access(self):
    admin = FskUser('oink', True)
    user = FskUser('oink', False)
    image = _create_image()[0]
    self.assertTrue(image.check_access(admin))
    self.assertTrue(image.check_access(user))
    self.assertTrue(image.check_access(None))
  
  def test_access_private(self):
    admin = FskUser('admin.oink', True)
    user = FskUser('user.oink', False)

    image, container, _, _ = _create_image()
    container.private = True

    self.assertFalse(image.check_access(None))
    self.assertTrue(image.check_access(admin))
    self.assertFalse(image.check_access(user))

    container.createdBy = user.username
    self.assertTrue(image.check_access(user))

  
  def test_update_access(self):
    admin = FskUser('admin.oink', True)
    user = FskUser('user.oink', False)

    image, container, _, _ = _create_image()
    self.assertTrue(image.check_update_access(admin))
    self.assertFalse(image.check_update_access(user))

    container.createdBy = user.username
    self.assertTrue(image.check_update_access(user))


  def test_schema(self):
    schema = ImageSchema()

    image = _create_image()[0]

    serialized = schema.dump(image)
    self.assertEqual(serialized.data['hash'], image.hash)

    entity = Entity(name='Test Hase')
    db.session.add(entity)
    db.session.commit()

    coll = Collection(name='Test Collection', entity_ref=entity)
    db.session.add(coll)
    db.session.commit()

    container = Container(name='Test Container', collection_ref=coll)
    db.session.add(container)
    db.session.commit()

    image.container_id=container.id
    db.session.commit()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['container'], str(container.id))
    self.assertEqual(serialized.data['containerName'], container.name)
    self.assertEqual(serialized.data['collection'], str(coll.id))
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)
    self.assertIsNone(serialized.data['deletedAt'])
    self.assertFalse(serialized.data['deleted'])

  def test_schema_tags(self):
    schema = ImageSchema()
    image = _create_image()[0]

    tag1 = Tag(name='v1', image_ref=image)
    db.session.add(tag1)
    db.session.commit()
    tag2 = Tag(name='v2', image_ref=image)
    db.session.add(tag2)
    db.session.commit()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertListEqual(serialized.data['tags'], ['v1', 'v2'])
    Tag.__table__.delete()