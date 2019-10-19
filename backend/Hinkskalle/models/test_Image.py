import unittest
from mongoengine import connect, disconnect

from Hinkskalle.models import Entity, Collection, Container, Image, ImageSchema, Tag

class TestImage(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()

  def test_image(self):
    image = Image(id='test-image')
    image.save()

    read_image = Image.objects.get(id='test-image')
    self.assertEqual(read_image.id, image.id)

  def test_container_ref(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    image = Image(id='test-image', container_ref=container)
    image.save()

    self.assertEqual(image.container(), container.id)
    self.assertEqual(image.containerName(), container.name)

    unlinked_image = Image(id='bad-image')
    unlinked_image.save()

    images = Image.objects(container_ref=container)
    self.assertEqual(len(images), 1)
    self.assertEqual(images.first(), image)


  
  def test_collection_ref(self):
    coll = Collection(id='test-collection', name='Test Collection')
    coll.save()

    container = Container(id='test-container', name='Test Container', collection_ref=coll)
    container.save()

    image = Image(id='test-image', container_ref=container)
    image.save()

    self.assertEqual(image.collection(), coll.id)
    self.assertEqual(image.collectionName(), coll.name)

  
  def test_entity_ref(self):
    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    coll = Collection(id='test-collection', name='Test Collection', entity_ref=entity)
    coll.save()

    container = Container(id='test-container', name='Test Container', collection_ref=coll)
    container.save()

    image = Image(id='test-image', container_ref=container)
    image.save()

    self.assertEqual(image.entity(), entity.id)
    self.assertEqual(image.entityName(), entity.name)

  def test_tags(self):
    image = Image(id='test-image')
    image.save()

    tag1 = Tag(name='v1', image_ref=image)
    tag1.save()
    tag2 = Tag(name='v2', image_ref=image)
    tag2.save()

    self.assertListEqual(image.tags(), ['v1', 'v2'])
    Tag.objects.delete()

  def test_schema(self):
    schema = ImageSchema()

    image = Image(id='test-image')
    image.save()

    serialized = schema.dump(image)
    self.assertEqual(serialized.data['id'], image.id)

    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    coll = Collection(id='test-collection', name='Test Collection', entity_ref=entity)
    coll.save()

    container = Container(id='test-container', name='Test Container', collection_ref=coll)
    container.save()

    image.container_ref=container 
    image.save()

    serialized = schema.dump(image)
    self.assertEqual(serialized.data['container'], container.id)
    self.assertEqual(serialized.data['containerName'], container.name)
    self.assertEqual(serialized.data['collection'], coll.id)
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], entity.id)
    self.assertEqual(serialized.data['entityName'], entity.name)

  def test_schema_tags(self):
    schema = ImageSchema()
    image = Image(id='test-image')
    image.save()

    tag1 = Tag(name='v1', image_ref=image)
    tag1.save()
    tag2 = Tag(name='v2', image_ref=image)
    tag2.save()

    serialized = schema.dump(image)
    self.assertListEqual(serialized.data['tags'], ['v1', 'v2'])
    Tag.objects.delete()