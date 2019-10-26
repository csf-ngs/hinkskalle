import unittest
from mongoengine import connect, disconnect
from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, Container, ContainerSchema, Image, Tag
from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle.fsk_api import FskUser

def _create_container(postfix='container'):
  coll, entity = _create_collection(f"test-collection-f{postfix}")

  container = Container(name=f"test-f{postfix}", collection_ref=coll)
  container.save()
  return container, coll, entity


class TestContainer(unittest.TestCase):
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

  def test_container(self):
    container, coll, entity = _create_container()

    read_container = Container.objects.get(name=container.name)
    self.assertEqual(read_container.id, container.id)
    self.assertTrue(abs(read_container.createdAt - datetime.utcnow()) < timedelta(seconds=1))

    self.assertEqual(read_container.collection(), coll.id)
    self.assertEqual(read_container.collectionName(), coll.name)

    self.assertEqual(read_container.entity(), entity.id)
    self.assertEqual(read_container.entityName(), entity.name)

  def test_images(self):
    container = _create_container()[0]

    image1 = Image(description='test-image-1', container_ref=container)
    image1.save()

    self.assertEqual(container.images().first().id, image1.id)

  def test_tag_image(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
    image1.save()

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.utcnow()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.updatedAt - datetime.utcnow()) < timedelta(seconds=1))
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1.1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.utcnow()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}"]
    )

    image2 = Image(hash='zwei', description='test-image-2', container_ref=container)
    image2.save()

    new_tag = container.tag_image('v2', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.utcnow()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}", f"v2:{image2.id}"]
    )

    new_tag = container.tag_image('v1.1', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    self.assertTrue(abs(new_tag.updatedAt - datetime.utcnow()) < timedelta(seconds=1))
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image2.id}", f"v2:{image2.id}"]
    )



  def test_get_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='test-image-1', container_ref=container)
    image1.save()
    image1tag1 = Tag(name='v1', image_ref=image1)
    image1tag1.save()
    self.assertDictEqual(container.imageTags(), { 'v1': str(image1.id) })

    image2 = Image(hash='test-image-2', container_ref=container)
    image2.save()
    image2tag1 = Tag(name='v2', image_ref=image2)
    image2tag1.save()
    self.assertDictEqual(container.imageTags(), { 'v1': str(image1.id), 'v2': str(image2.id) })

    invalidTag = Tag(name='v2', image_ref=image1)
    invalidTag.save()
    with self.assertRaisesRegex(Exception, 'Tag v2.*already set'):
      container.imageTags()
    

  def test_access(self):
    admin = FskUser('oink', True)
    user = FskUser('oink', False)

    container, collection, entity = _create_container()
    self.assertTrue(container.check_access(admin))
    self.assertFalse(container.check_access(user))

    container, collection, entity = _create_container('owned')
    entity.createdBy='oink'
    entity.save()
    collection.createdBy='oink'
    collection.save()
    container.createdBy='oink'
    self.assertTrue(container.check_access(user))

    container.createdBy='muh'
    self.assertFalse(container.check_access(user))

    container, collection, entity = _create_container('default')
    entity.name='default'
    entity.save()
    collection.createdBy='oink'
    collection.save()
    container.createdBy='oink'
    self.assertTrue(container.check_access(user))

    container.createdBy='muh'
    self.assertFalse(container.check_access(user))


  def test_schema(self):
    entity = Entity(name='test-hase')
    entity.save()

    coll = Collection(name='test-collection', entity_ref=entity)
    coll.save()

    container = Container(name='test-container', collection_ref=coll)
    container.save()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertEqual(serialized.data['id'], str(container.id))
    self.assertEqual(serialized.data['name'], container.name)
    self.assertEqual(serialized.data['private'], False)
    self.assertEqual(serialized.data['readOnly'], False)

    serialized = schema.dump(container)
    self.assertEqual(serialized.data['collection'], str(coll.id))
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)
  
  def test_schema_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
    image1.save()
    image1tag1 = Tag(name='v1', image_ref=image1)
    image1tag1.save()
    image2 = Image(hash='zwei', description='test-image-2', container_ref=container)
    image2.save()
    image2tag1 = Tag(name='v2', image_ref=image2)
    image2tag1.save()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertDictEqual(serialized.data['imageTags'], { 'v1': str(image1.id), 'v2': str(image2.id) })