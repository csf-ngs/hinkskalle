from datetime import datetime, timedelta

from Hinkskalle.models import Entity, Collection, Container, ContainerSchema, Image, Tag
from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle.tests.model_base import ModelBase, _create_user
from Hinkskalle import db


def _create_container(postfix='container'):
  coll, entity = _create_collection(f"test-collection-f{postfix}")

  container = Container(name=f"test-f{postfix}", collection_id=coll.id)
  db.session.add(container)
  db.session.commit()
  return container, coll, entity


class TestContainer(ModelBase):

  def test_container(self):
    container, coll, entity = _create_container()

    read_container = Container.query.filter_by(name=container.name).one()
    self.assertEqual(read_container.id, container.id)
    self.assertTrue(abs(read_container.createdAt - datetime.now()) < timedelta(seconds=1))

    self.assertEqual(read_container.collection(), coll.id)
    self.assertEqual(read_container.collectionName(), coll.name)

    self.assertEqual(read_container.entity(), entity.id)
    self.assertEqual(read_container.entityName(), entity.name)

  def test_images(self):
    container = _create_container()[0]

    image1 = Image(description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()

    self.assertEqual(container.images_ref.one().id, image1.id)
  
  def test_count(self):
    container, collection, entity = _create_container()
    self.assertEqual(container.size(), 0)

    nosave = Container(name='nosave', collection_id=collection.id)
    self.assertEqual(nosave.size(), 0)

    image1 = Image(container_id=container.id)
    db.session.add(image1)
    db.session.commit()
    self.assertEqual(container.size(), 1)

    other_container = _create_container('other')[0]
    other_image = Image(container_id=other_container.id)
    db.session.add(other_image)
    db.session.commit()
    self.assertEqual(container.size(), 1)

  def test_tag_image(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.now()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.query.filter(Tag.image_id.in_([ c.id for c in container.images_ref ])).all()
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.updatedAt - datetime.now()) < timedelta(seconds=1))
    tags = Tag.query.filter(Tag.image_id.in_([ c.id for c in container.images_ref ])).all()
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}"]
    )

    new_tag = container.tag_image('v1.1', image1.id)
    self.assertEqual(new_tag.image_ref.id, image1.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.now()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.query.filter(Tag.image_id.in_([ c.id for c in container.images_ref ])).all()
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}"]
    )

    image2 = Image(hash='zwei', description='test-image-2', container_id=container.id)
    db.session.add(image2)
    db.session.commit()

    new_tag = container.tag_image('v2', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    self.assertTrue(abs(new_tag.createdAt - datetime.now()) < timedelta(seconds=1))
    self.assertIsNone(new_tag.updatedAt)
    tags = Tag.query.filter(Tag.image_id.in_([ c.id for c in container.images_ref ])).all()
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image1.id}", f"v2:{image2.id}"]
    )

    new_tag = container.tag_image('v1.1', image2.id)
    self.assertEqual(new_tag.image_ref.id, image2.id)
    self.assertTrue(abs(new_tag.updatedAt - datetime.now()) < timedelta(seconds=1))
    tags = Tag.query.filter(Tag.image_id.in_([ c.id for c in container.images_ref ])).all()
    self.assertListEqual(
      [f"{tag.name}:{tag.image_ref.id}" for tag in tags ],
      [f"v1:{image1.id}", f"v1.1:{image2.id}", f"v2:{image2.id}"]
    )



  def test_get_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()
    image1tag1 = Tag(name='v1', image_id=image1.id)
    db.session.add(image1tag1)
    db.session.commit()
    self.assertDictEqual(container.imageTags(), { 'v1': str(image1.id) })

    image2 = Image(hash='test-image-2', container_id=container.id)
    db.session.add(image2)
    db.session.commit()
    image2tag1 = Tag(name='v2', image_id=image2.id)
    db.session.add(image2tag1)
    db.session.commit()
    self.assertDictEqual(container.imageTags(), { 'v1': str(image1.id), 'v2': str(image2.id) })

    invalidTag = Tag(name='v2', image_id=image1.id)
    db.session.add(invalidTag)
    db.session.commit()
    with self.assertRaisesRegex(Exception, 'Tag v2.*already set'):
      container.imageTags()
    

  def test_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)
    other_user = _create_user(name='user.muh', is_admin=False)

    container, collection, entity = _create_container()
    self.assertTrue(container.check_access(admin))
    self.assertFalse(container.check_access(user))

    container, collection, entity = _create_container('owned')
    entity.owner=user
    collection.owner=user
    container.owner=user
    self.assertTrue(container.check_access(user))

    container.owner=other_user
    self.assertTrue(container.check_access(user))

    container, collection, entity = _create_container('default')
    entity.name='default'
    collection.owner=user
    container.owner=user
    self.assertTrue(container.check_access(user))

    container.owner=other_user
    self.assertTrue(container.check_access(user))
  
  def test_update_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)

    container, _, _ = _create_container()
    self.assertTrue(container.check_update_access(admin))
    self.assertFalse(container.check_update_access(user))

    container.owner = user
    self.assertTrue(container.check_update_access(user))


  def test_schema(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()

    coll = Collection(name='test-collection', entity_id=entity.id)
    db.session.add(coll)
    db.session.commit()

    container = Container(name='test-container', collection_id=coll.id)
    db.session.add(container)
    db.session.commit()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertEqual(serialized.data['id'], str(container.id))
    self.assertEqual(serialized.data['name'], container.name)
    self.assertEqual(serialized.data['private'], False)
    self.assertEqual(serialized.data['readOnly'], False)
    self.assertIsNone(serialized.data['deletedAt'])
    self.assertFalse(serialized.data['deleted'])
    self.assertEqual(serialized.data['stars'], 0)

    serialized = schema.dump(container)
    self.assertEqual(serialized.data['collection'], str(coll.id))
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)
  
  def test_schema_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()
    image1tag1 = Tag(name='v1', image_id=image1.id)
    db.session.add(image1tag1)
    db.session.commit()
    image2 = Image(hash='zwei', description='test-image-2', container_id=container.id)
    db.session.add(image2)
    db.session.commit()
    image2tag1 = Tag(name='v2', image_id=image2.id)
    db.session.add(image2tag1)
    db.session.commit()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertDictEqual(serialized.data['imageTags'], { 'v1': str(image1.id), 'v2': str(image2.id) })