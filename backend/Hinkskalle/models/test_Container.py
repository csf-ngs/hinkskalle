import unittest
from mongoengine import connect, disconnect

from Hinkskalle.models import Entity, Collection, Container, ContainerSchema, Image, Tag

class TestContainer(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    disconnect()
    connect('mongoenginetest', host='mongomock://localhost')
  
  @classmethod
  def tearDownClass(cls):
    disconnect()

  def test_container(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    read_container = Container.objects.get(id='test-container')
    self.assertEqual(read_container.id, container.id)
  
  def test_collection_ref(self):
    coll = Collection(id='test-collection', name='Test Collection')
    coll.save()

    container = Container(id='test-container', name='Test Container', collection_ref=coll)
    container.save()

    self.assertEqual(container.collection(), coll.id)
    self.assertEqual(container.collectionName(), coll.name)

  
  def test_entity_ref(self):
    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    coll = Collection(id='test-collection', name='Test Collection', entity_ref=entity)
    coll.save()

    container = Container(id='test-container', name='Test Container', collection_ref=coll)
    container.save()

    self.assertEqual(container.entity(), entity.id)
    self.assertEqual(container.entityName(), entity.name)

  def test_images(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    image1 = Image(id='test-image-1', container_ref=container)
    image1.save()

    self.assertEqual(container.images().first().id, image1.id)

  def test_tag_image(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    image1 = Image(id='test-image-1', container_ref=container)
    image1.save()

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1.1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}"]
    )

    image2 = Image(id='test-image-2', container_ref=container)
    image2.save()

    new_tag = container.tag_image('v2', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}", f"v2:{image2.id}"]
    )

    new_tag = container.tag_image('v1.1', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    tags = Tag.objects(image_ref__in=container.images())
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image2.id}", f"v2:{image2.id}"]
    )

    Tag.objects.delete()


  def test_get_tags(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    image1 = Image(id='test-image-1', container_ref=container)
    image1.save()
    image1tag1 = Tag(name='v1', image_ref=image1)
    image1tag1.save()
    self.assertDictEqual(container.imageTags(), { 'v1': image1.id })

    image2 = Image(id='test-image-2', container_ref=container)
    image2.save()
    image2tag1 = Tag(name='v2', image_ref=image2)
    image2tag1.save()
    self.assertDictEqual(container.imageTags(), { 'v1': image1.id, 'v2': image2.id })

    invalidTag = Tag(name='v2', image_ref=image1)
    invalidTag.save()
    with self.assertRaisesRegex(Exception, 'Tag v2.*already set'):
      container.imageTags()
    
    Tag.objects.delete()


  def test_schema(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertEqual(serialized.data['id'], container.id)
    self.assertEqual(serialized.data['name'], container.name)
    self.assertEqual(serialized.data['private'], False)
    self.assertEqual(serialized.data['readOnly'], False)

    entity = Entity(id='test-hase', name='Test Hase')
    entity.save()

    coll = Collection(id='test-collection', name='Test Collection', entity_ref=entity)
    coll.save()

    container.collection_ref=coll
    container.save()

    serialized = schema.dump(container)
    self.assertEqual(serialized.data['collection'], coll.id)
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], entity.id)
    self.assertEqual(serialized.data['entityName'], entity.name)
  
  def test_schema_tags(self):
    container = Container(id='test-container', name='Test Container')
    container.save()

    image1 = Image(id='test-image-1', container_ref=container)
    image1.save()
    image1tag1 = Tag(name='v1', image_ref=image1)
    image1tag1.save()
    image2 = Image(id='test-image-2', container_ref=container)
    image2.save()
    image2tag1 = Tag(name='v2', image_ref=image2)
    image2tag1.save()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertDictEqual(serialized.data['imageTags'], { 'v1': 'test-image-1', 'v2': 'test-image-2' })
    Tag.objects.delete()