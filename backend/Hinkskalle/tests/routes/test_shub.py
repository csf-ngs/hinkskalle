
import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle import db
from Hinkskalle.models import Tag
from Hinkskalle.tests.models.test_Image import _create_image

class TestEntities(RouteBase):
  def test_manifest(self):
    image, _, _, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    entity.name='default'
    db.session.commit()

    ret = self.client.get(f"/api/container/{image.collectionName()}/{image.containerName()}:latest")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json()
    self.assertDictEqual(data, {
      'image': f"http://localhost/v1/imagefile/default/{image.collectionName()}/{image.containerName()}:latest",
      'name': image.containerName(),
      'tag': latest_tag.name,
      #'version': None,
      #'commit': None,
    })

  def test_manifest_private(self):
    image, container, _, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)
    entity.name='default'
    container.private=True

    db.session.commit()

    ret = self.client.get(f"/api/container/{image.collectionName()}/{image.containerName()}:latest")
    self.assertEqual(ret.status_code, 403)

