
import unittest
import os
import json
from Hinkskalle import create_app

from Hinkskalle.models import Entity, Collection

from Hinkskalle.tests.models.test_Collection import _create_collection

class TestCollections(unittest.TestCase):
  app = None
  client = None
  @classmethod
  def setUpClass(cls):
    os.environ['MONGODB_HOST']='mongomock://localhost'
  
  def setUp(self):
    self.app = create_app()
    self.client = self.app.test_client()
  def tearDown(self):
    Entity.objects.delete()
    Collection.objects.delete()
  
  def test_get(self):
    coll, entity = _create_collection()

    ret = self.client.get(f"/v1/collections/{coll.entityName()}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_default(self):
    coll, entity = _create_collection()
    entity.name=''
    entity.save()

    ret = self.client.get(f"/v1/collections//{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
