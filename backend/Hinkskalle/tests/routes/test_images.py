import unittest
import json
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth

from Hinkskalle.models import Image, Tag
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.tests.models.test_Container import _create_container

class TestImages(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/containers/what/ev/er/images')
    self.assertEqual(ret.status_code, 401)
  
  def test_list(self):
    image1, container, collection, entity = _create_image('img1')
    image2 = _create_image('img2')[0]
    image2.container_ref=container
    image2.save()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['id'] for c in json ], [ str(image1.id), str(image2.id) ] )
  
  def test_list_user(self):
    image1, container, collection, entity = _create_image('img1')
    image2 = _create_image('img2')[0]
    image2.container_ref=container
    image2.save()
    container.createdBy='test.hase'
    container.save()
    collection.createdBy='test.hase'
    collection.save()
    entity.createdBy='test.hase'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['id'] for c in json ], [ str(image1.id), str(image2.id) ] )
  
  def test_list_user_other(self):
    image1, container, collection, entity = _create_image('img1')
    container.createdBy='test.kuh'
    container.save()
    collection.createdBy='test.hase'
    collection.save()
    entity.createdBy='test.hase'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/containers/{entity.name}/{collection.name}/{container.name}/images")
    self.assertEqual(ret.status_code, 403)


  def test_get_latest(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}/{image.collectionName()}/{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))
    self.assertListEqual(data['tags'], ['latest'])
  
  def test_get_default_entity(self):
    image, _, _, entity = _create_image()
    entity.name='default'
    entity.save()

    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images//{image.collectionName()}/{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))

  def test_get_default_entity_single(self):
    image, _, _, entity = _create_image()
    entity.name='default'
    entity.save()

    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.collectionName()}/{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))
  
  def test_get_default_collection(self):
    image, _, collection, entity = _create_image()
    collection.name='default'
    collection.save()

    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images/{image.entityName()}//{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))
  
  def test_get_default_collection_default_entity(self):
    image, _, collection, entity = _create_image()
    entity.name = 'default'
    entity.save()
    collection.name='default'
    collection.save()

    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    ret = self.client.get(f"/v1/images///{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))

    ret = self.client.get(f"/v1/images//{image.containerName()}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(image.id))

    ret = self.client.get(f"/v1/images/{image.containerName()}")
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

  def test_get_hash_not_found(self):
    first_image = _create_image(hash='sha256.oink')[0]
    first_image.save()

    ret = self.client.get(f"/v1/images/{first_image.entityName()}/{first_image.collectionName()}/{first_image.containerName()}:sha256.muh")
    self.assertEqual(ret.status_code, 404)

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
  
  def test_create_noauth(self):
    ret = self.client.post("/v1/images")
    self.assertEqual(ret.status_code, 401)

  def test_create(self):
    container, _, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': 'sha256.oink',
        'container': str(container.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['hash'], 'sha256.oink')
    self.assertEqual(data['container'], str(container.id))
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_uploaded(self):
    container, _, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': 'sha256.oink',
        'container': str(container.id),
        'uploaded': True,
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertTrue(data['uploaded'])
    self.assertDictEqual(container.imageTags(), {
      'latest': data['id']
    })


  def test_create_not_unique(self):
    image, container, _, _ = _create_image()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': image.hash,
        'container': str(container.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_container(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': 'sha256.oink',
        'container': 'oink oink',
      })
    self.assertEqual(ret.status_code, 500)
  
  def test_reuse_image(self):
    image, _, _, _ = _create_image()
    image.uploaded=True
    image.location=__file__
    image.size=999
    image.save()
    other_container, _, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': image.hash,
        'container': str(other_container.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertTrue(data['uploaded'])
    self.assertEqual(data['size'], image.size)
    other_image = Image.objects.get(id=data['id'])
    self.assertEqual(other_image.location, image.location)
    self.assertDictEqual(other_container.imageTags(), {
      'latest': str(other_image.id)
    })

  def test_reuse_image_not_uploaded(self):
    image, _, _, _ = _create_image()
    image.uploaded=False
    image.location=__file__
    image.save()
    other_container, _, _ = _create_container()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': image.hash,
        'container': str(other_container.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertFalse(data['uploaded'])
    self.assertIsNone(data['size'])
    self.assertDictEqual(other_container.imageTags(), {})

  def test_create_user(self):
    container, coll, entity = _create_container()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.hase'
    coll.save()
    container.createdBy = 'test.hase'
    container.save()

    with fake_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': 'sha256.oink',
        'container': str(container.id),
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_other(self):
    container, coll, entity = _create_container()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.hase'
    coll.save()
    container.createdBy = 'test.muh'
    container.save()

    with fake_auth(self.app):
      ret = self.client.post('/v1/images', json={
        'hash': 'sha256.oink',
        'container': str(container.id),
      })
    self.assertEqual(ret.status_code, 403)
