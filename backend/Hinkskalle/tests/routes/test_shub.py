
import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.models import Tag
from Hinkskalle.tests.models.test_Image import _create_image

class TestEntities(RouteBase):
  def test_manifest(self):
    image, _, _, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    entity.name=''
    entity.save()

    ret = self.client.get(f"/api/container/{image.collectionName()}/{image.containerName()}:latest")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json()
    self.assertDictEqual(data, {
      'image': f"http://localhost/v1/imagefile//{image.collectionName()}/{image.containerName()}:latest",
      'name': image.containerName(),
      'tag': latest_tag.name,
      #'version': None,
      #'commit': None,
    })
  
  def test_pull(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(b"Hello Dorian!")
    tmpf.flush()
    image.location = tmpf.name
    image.save()

