
import unittest
import os
import json
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.models.test_Collection import _create_collection

class TestCollections(RouteBase):
  
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
