import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, Container, Image, ImageSchema, Tag

from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle.fsk_api import FskUser

def _create_image(hash='sha256.oink', postfix='container'):
  try:
    coll = Collection.objects.get(name=f"test-coll-{postfix}")
    entity = coll.entity_ref
  except:
    coll, entity = _create_collection(f"test-coll-{postfix}")

  try:
    container = Container.objects.get(name=f"test-{postfix}")
  except:
    container = Container(name=f"test-{postfix}", collection_ref=coll)
    container.save()

  image = Image(container_ref=container, hash=hash)
  image.save()
  return image, container, coll, entity

class TestImage(unittest.TestCase):
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
    Container.objects.delete()
    Image.objects.delete()
    Tag.objects.delete()


  def test_image(self):
    entity = Entity(name='test-hase')
    entity.save()

    coll = Collection(name='test-collection', entity_ref=entity)
    coll.save()

    container = Container(name='test-container',collection_ref=coll)
    container.save()

    image = Image(description='test-image', container_ref=container)
    image.save()

    read_image = Image.objects.get(id=image.id)
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
    tag1.save()
    tag2 = Tag(name='v2', image_ref=image)
    tag2.save()

    self.assertListEqual(image.tags(), ['v1', 'v2'])
    Tag.objects.delete()
  
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
    entity.save()

    coll = Collection(name='Test Collection', entity_ref=entity)
    coll.save()

    container = Container(name='Test Container', collection_ref=coll)
    container.save()

    image.container_ref=container 
    image.save()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['container'], str(container.id))
    self.assertEqual(serialized.data['containerName'], container.name)
    self.assertEqual(serialized.data['collection'], str(coll.id))
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)

  def test_schema_tags(self):
    schema = ImageSchema()
    image = _create_image()[0]

    tag1 = Tag(name='v1', image_ref=image)
    tag1.save()
    tag2 = Tag(name='v2', image_ref=image)
    tag2.save()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertListEqual(serialized.data['tags'], ['v1', 'v2'])
    Tag.objects.delete()