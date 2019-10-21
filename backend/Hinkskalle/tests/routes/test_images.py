import unittest
import os
import json
import tempfile
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.models import Image, Tag
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.tests.models.test_Container import _create_container

class TestImages(RouteBase):
  def test_get_latest(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))
    self.assertListEqual(data['tags'], ['latest'])
  
  def test_get_default(self):
    image, _, _, entity = _create_image()
    entity.name=''
    entity.save()

    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images//{image.collectionName()}/{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))


  def test_get_with_tag(self):
    v1_image = _create_image()[0]
    v1_tag = Tag(name='v1', image_ref=v1_image)
    v1_tag.save()

    latest_image = _create_image(hash='sha256.moo')[0]
    latest_tag = Tag(name='latest', image_ref=latest_image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{v1_image.entityName()}/{v1_image.collectionName()}/{v1_image.containerName()}:{v1_tag.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(v1_image.id))
    self.assertListEqual(data['tags'], ['v1'])
  
  def test_get_hash(self):
    first_image = _create_image(hash='sha256.oink')[0]
    first_image.save()

    second_image = _create_image(hash='sha256.moo')[0]
    second_image.save()

    ret = self.client.get(f"/v1/images/{first_image.entityName()}/{first_image.collectionName()}/{first_image.containerName()}:{first_image.hash}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(first_image.id))

  def test_reset_uploaded(self):
    image = _create_image()[0]
    image.location = '/some/where'
    image.uploaded = True
    image.save()
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{image.hash}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertFalse(data['uploaded'])
    read_image = Image.objects.get(id=image.id)
    self.assertIsNone(read_image.location)

    image.location = None
    image.uploaded = True
    image.save()
    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{image.hash}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertFalse(data['uploaded'])
    
  def test_pull(self):
    image = _create_image()[0]
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
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    ret.close() # avoid unclosed filehandle warning

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    ret.close() # avoid unclosed filehandle warning

    tmpf.close()

  def test_pull_default_entity(self):
    image, _, _, entity = _create_image()
    image.uploaded=True
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    entity.name=''
    entity.save()

    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(b"Hello default Entity!")
    tmpf.flush()
    image.location=tmpf.name
    image.save()

    ret = self.client.get(f"/v1/imagefile//{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close()
    tmpf.close()