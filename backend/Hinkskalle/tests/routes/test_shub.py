
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
  
  def test_manifest(self):
    image = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/api/container/{image.collectionName()}/{image.containerName()}:latest")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json()
    self.assertDictEqual(data, {
      'image': '',
      'name': image.containerName(),
      'tag': latest_tag.name,
      #'version': None,
      #'commit': None,
    })
  
  def test_pull(self):
    image = _create_image() 
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(b"Hello Dorian!")
    tmpf.flush()
    image.location = tmpf.name
    image.save()

