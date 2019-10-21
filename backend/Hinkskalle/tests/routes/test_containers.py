
import unittest
import os
import json
import tempfile
from Hinkskalle import create_app

from Hinkskalle.models import Entity, Collection, Container, Image, Tag
from Hinkskalle.tests.models.test_Container import _create_container

class TestContainers(unittest.TestCase):
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
  
  def test_get(self):
    container, coll, entity = _create_container()

    ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))
  
  def test_get_default(self):
    container, coll, entity = _create_container()
    entity.name=''
    entity.save()

    ret = self.client.get(f"/v1/containers//{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(container.id))


  
