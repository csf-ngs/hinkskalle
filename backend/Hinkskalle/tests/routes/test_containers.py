
import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.models.test_Container import _create_container

class TestContainers(RouteBase):
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


  
