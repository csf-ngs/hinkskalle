
import unittest
import os
import json
import tempfile
from Hinkskalle import create_app

from Hinkskalle.models import Entity, Collection, Container, Image, Tag
from Hinkskalle.tests.models.test_Image import _create_image

class TestEntities(unittest.TestCase):
  app = None
  client = None
  @classmethod
  def setUpClass(cls):
    os.environ['MONGODB_HOST']='mongomock://localhost'
  
  def setUp(self):
    self.app = create_app()
    self.app.config['TESTING'] = True
    self.client = self.app.test_client()

  def tearDown(self):
    Entity.objects.delete()
    Collection.objects.delete()
    Container.objects.delete()
    Image.objects.delete()
    Tag.objects.delete()

  def test_get_latest(self):
    image = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}")
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))
    self.assertListEqual(data['tags'], ['latest'])

  def test_get_with_tag(self):
    v1_image = _create_image()
    v1_tag = Tag(name='v1', image_ref=v1_image)
    v1_tag.save()

    latest_image = _create_image(hash='sha256.moo')
    latest_tag = Tag(name='latest', image_ref=latest_image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{v1_image.entityName()}/{v1_image.collectionName()}/{v1_image.containerName()}:{v1_tag.name}")
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(v1_image.id))
    self.assertListEqual(data['tags'], ['v1'])
  
  def test_get_hash(self):
    first_image = _create_image(hash='sha256.oink')
    first_image.save()

    second_image = _create_image(hash='sha256.moo')
    second_image.save()

    ret = self.client.get(f"/v1/images/{first_image.entityName()}/{first_image.collectionName()}/{first_image.containerName()}:{first_image.hash}")
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(first_image.id))
  
  def test_reset_uploaded(self):
    image = _create_image()
    image.location = '/some/where'
    image.uploaded = True
    image.save()
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{image.hash}")
    data = ret.get_json().get('data')
    self.assertFalse(data['uploaded'])
    read_image = Image.objects.get(id=image.id)
    self.assertIsNone(read_image.location)

    image.location = None
    image.uploaded = True
    image.save()
    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{image.hash}")
    data = ret.get_json().get('data')
    self.assertFalse(data['uploaded'])



    
  def test_pull(self):
    image = _create_image()
    image.uploaded=True
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(b"Hello Dorian!")
    tmpf.flush()
    image.location=tmpf.name
    image.save()

    ret = self.client.get(f"/v1/imagefile/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    ret.close() # avoid unclosed filehandle warning

    ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    ret.close() # avoid unclosed filehandle warning

    tmpf.close()