from Hinkskalle.models.Manifest import Manifest
from datetime import datetime, timedelta
from typing import Tuple
from unittest.case import skip

from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Container import ContainerTypes
from Hinkskalle.models import Collection, Container, ContainerSchema, Image, Tag
from .test_Image import _create_image
from ..model_base import ModelBase
from .._util import _create_user, _create_container, _create_image

from Hinkskalle import db


class TestContainer(ModelBase):

  def test_container(self):
    container, coll, entity = _create_container()

    read_container = Container.query.filter_by(name=container.name).one()
    self.assertEqual(read_container.id, container.id)
    self.assertTrue(abs(read_container.createdAt - datetime.now()) < timedelta(seconds=1))

    self.assertEqual(read_container.collection, coll.id)
    self.assertEqual(read_container.collectionName, coll.name)

    self.assertEqual(read_container.entity, entity.id)
    self.assertEqual(read_container.entityName, entity.name)
  
  def test_container_case(self):
    container, _, _ = _create_container('TestContainer')
    read_container = Container.query.get(container.id)
    self.assertEqual(container.name, 'test-testcontainer')

  def test_images(self):
    container = _create_container()[0]

    image1 = Image(description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()

    self.assertEqual(container.images_ref.one().id, image1.id)
  
  def test_count(self):
    container, collection, entity = _create_container()
    self.assertEqual(container.size, 0)

    nosave = Container(name='nosave', collection_id=collection.id)
    self.assertEqual(nosave.size, 0)

    image1 = Image(container_id=container.id, uploaded=True)
    db.session.add(image1)
    db.session.commit()
    self.assertEqual(container.size, 1)

    other_container = _create_container('other')[0]
    other_image = Image(container_id=other_container.id, uploaded=True)
    db.session.add(other_image)
    db.session.commit()
    self.assertEqual(container.size, 1)

    image2 = Image(container_id=container.id, hide=True)
    db.session.add(image2)
    self.assertEqual(container.size, 1)

    image3 = Image(container_id=container.id, uploaded=False)
    db.session.add(image3)
    self.assertEqual(container.size, 1)
  
  def test_get_tag(self):
    container = _create_container()[0]
    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
    image2 = Image(hash='zwo', description='test-image-2', container_ref=container)

    tag1 = Tag(image_ref=image1, name='v1')
    tag2 = Tag(image_ref=image2, name='v2')

    db.session.add(image1)
    db.session.add(image2)
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()

    tag = container.get_tag('v1')
    self.assertEqual(tag.name, 'v1')
    self.assertEqual(tag.image_id, image1.id)
  
  def test_get_tag_not_found(self):
    container = _create_container()[0]
    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
    tag1 = Tag(image_ref=image1, name='v1')
    db.session.add(image1)
    db.session.add(tag1)
    db.session.commit()

    self.assertIsNone(container.get_tag('oink'))

  
  def test_get_tag_duplicate(self):
    container = _create_container()[0]
    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
    image2 = Image(hash='zwo', description='test-image-2', container_ref=container)

    tag1 = Tag(image_ref=image1, name='v1')
    tag2 = Tag(image_ref=image2, name='v1')

    db.session.add(image1)
    db.session.add(image2)
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()

    with self.assertRaisesRegex(Exception, r'Multiple'):
      tag = container.get_tag('v1')
  
  def test_get_arch_tag(self):
    container = _create_container()[0]
    image1 = Image(hash='eins', arch='c64', description='test-image-1', container_ref=container)
    image2 = Image(hash='zwo', arch='amiga', description='test-image-2', container_ref=container)

    tag1 = Tag(image_ref=image1, name='v1')
    tag2 = Tag(image_ref=image2, name='v1')

    db.session.add(image1)
    db.session.add(image2)
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()

    tag = container.get_tag('v1', arch='c64')
    self.assertEqual(tag.id, tag1.id)
    self.assertEqual(tag.image_id, image1.id)



  def test_tag_image(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_ref=container)
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

  def test_tag_image_case(self):
    container = _create_container()[0]
    image1 = Image(hash='eins', description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()

    new_tag = container.tag_image('TestHase', image1.id)
    dbtag = Tag.query.get(new_tag.id)
    self.assertEqual(dbtag.name, 'testhase')

  def test_tag_image_arch(self):
    container = _create_container()[0]
    image1 = Image(hash='test-image-1', container_ref=container, arch='c64')
    db.session.add(image1)
    db.session.commit()

    container.tag_image('v1', image1.id, arch='c64')
    self.assertDictEqual(container.archImageTags, {
      'c64': { 'v1': str(image1.id) }
    })

    image2 = Image(hash='test-image-2', container_ref=container)
    db.session.add(image2)
    db.session.commit()

    tag2 = container.tag_image('v1', image2.id, arch='amiga')
    self.assertEqual(image2.arch, 'amiga')
    self.assertDictEqual(container.archImageTags, {
      'c64': { 'v1': str(image1.id) },
      'amiga': { 'v1': str(image2.id) },
    })

    db.session.delete(tag2)
    container.tag_image('v1', image2.id, arch='c64')
    self.assertEqual(image2.arch, 'c64')
    self.assertDictEqual(container.archImageTags, {
      'c64': { 'v1': str(image2.id) },
    })

  def test_tag_default_arch(self):
    container = _create_container()[0]
    image1 = Image(hash='test-image-1', container_ref=container, arch=None)
    tag1 = Tag(image_ref=image1, container_ref=container, name='noarch')
    tag2 = Tag(image_ref=image1, container_ref=container, name='yesarch', arch='c64')
    db.session.add(image1)
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()

    self.assertDictEqual(container.archImageTags, {
      'c64': { 'yesarch': str(image1.id) },
      self.app.config['DEFAULT_ARCH']: { 'noarch': str(image1.id) },
    })
    print(container.archImageTags)

    



  def test_get_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()
    image1tag1 = Tag(name='v1', image_ref=image1)
    db.session.add(image1tag1)
    db.session.commit()
    self.assertDictEqual(container.imageTags, { 'v1': str(image1.id) })

    image2 = Image(hash='test-image-2', container_id=container.id)
    db.session.add(image2)
    db.session.commit()
    image2tag1 = Tag(name='v2', image_ref=image2)
    db.session.add(image2tag1)
    db.session.commit()
    self.assertDictEqual(container.imageTags, { 'v1': str(image1.id), 'v2': str(image2.id) })

    #invalidTag = Tag(name='v2', image_id=image1.id)
    #db.session.add(invalidTag)
    #db.session.commit()
    #with self.assertRaisesRegex(Exception, 'Tag v2.*already set'):
    #  container.imageTags()
    
  def test_get_tags_arch_required(self):
    container = _create_container()[0]
    image1 = Image(hash='test-image-1', container_ref=container)
    image2 = Image(hash='test-image-2', container_ref=container)
    db.session.add(image1)
    db.session.add(image2)
    db.session.commit()
    container.tag_image('v1', image1.id, arch='c64')
    container.tag_image('v1', image2.id, arch='apple')

    with self.assertRaisesRegex(Exception, 'Tag v1 has multiple architectures'):
      container.imageTags

  def test_get_arch_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='test-image-1', container_ref=container, arch='powerpc')
    image1tag1 = Tag(name='v1', image_ref=image1, arch='powerpc')
    db.session.add(image1)
    db.session.add(image1tag1)
    db.session.commit()

    self.assertDictEqual(container.archImageTags, {
      'powerpc': { 'v1': str(image1.id) }
    })

    image2 = Image(hash='test-image-2', container_ref=container, arch='alpha')
    image2tag1 = Tag(name='v1', image_ref=image2, arch='alpha')
    db.session.add(image2tag1)
    db.session.commit()

    self.assertDictEqual(container.archImageTags, {
      'powerpc': {'v1': str(image1.id)},
      'alpha': {'v1': str(image2.id)},
    })

    no_arch = Image(hash='test-image-3', container_ref=container)
    no_arch_tag = Tag(name='v1', image_ref=no_arch)
    db.session.add(no_arch_tag)
    db.session.commit()

    self.assertDictEqual(container.archImageTags, {
      'powerpc': {'v1': str(image1.id)},
      'alpha': {'v1': str(image2.id)},
      'amd64': {'v1': str(no_arch.id)},
    })

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
    self.assertEqual(serialized['id'], str(container.id))
    self.assertEqual(serialized['name'], container.name)
    self.assertEqual(serialized['private'], False)
    self.assertEqual(serialized['readOnly'], False)
    self.assertIsNone(serialized['deletedAt'])
    self.assertFalse(serialized['deleted'])
    self.assertEqual(serialized['stars'], 0)

    serialized = schema.dump(container)
    self.assertEqual(serialized['collection'], str(coll.id))
    self.assertEqual(serialized['collectionName'], coll.name)
    self.assertEqual(serialized['entity'], str(entity.id))
    self.assertEqual(serialized['entityName'], entity.name)
  
  def test_schema_tags(self):
    container = _create_container()[0]

    image1 = Image(hash='eins', description='test-image-1', container_id=container.id)
    db.session.add(image1)
    db.session.commit()
    image1tag1 = Tag(name='v1', image_ref=image1)
    db.session.add(image1tag1)
    db.session.commit()
    image2 = Image(hash='zwei', description='test-image-2', container_id=container.id)
    db.session.add(image2)
    db.session.commit()
    image2tag1 = Tag(name='v2', image_ref=image2)
    db.session.add(image2tag1)
    db.session.commit()

    schema = ContainerSchema()
    serialized = schema.dump(container)
    self.assertDictEqual(serialized['imageTags'], { 'v1': str(image1.id), 'v2': str(image2.id) })
  
  def test_type(self):
    image = _create_image()[0]
    self.assertEqual(image.container_ref.type, ContainerTypes.singularity.name)

    image.media_type='application/vnd.oci.image.layer.v1.tar+gzip'
    self.assertEqual(image.container_ref.type, ContainerTypes.generic.name)

    image.media_type='application/vnd.docker.image.rootfs.diff.tar.gzip'
    self.assertEqual(image.container_ref.type, ContainerTypes.docker.name)

    image2 = _create_image(hash='sha256.gunz')[0]
    image2.container_ref=image.container_ref
    image2.media_type = Image.singularity_media_type
    image.media_type = Image.singularity_media_type

    self.assertEqual(image.container_ref.type, ContainerTypes.singularity.name)
    image2.media_type='application/vnd.oci.image.layer.v1.tar+gzip'
    self.assertEqual(image.container_ref.type, ContainerTypes.mixed.name)
  
  def test_type_hidden(self):
    image = _create_image()[0]
    self.assertEqual(image.container_ref.type, ContainerTypes.singularity.name)

    image2 = _create_image(hash='sha256.grunz')[0]
    image2.container_ref=image.container_ref
    image2.media_type = 'application/vnd.oci.image.layer.v1.tar+gzip'
    self.assertEqual(image.container_ref.type, ContainerTypes.mixed.name)
    image2.hide = True
    self.assertEqual(image.container_ref.type, ContainerTypes.singularity.name)


    





