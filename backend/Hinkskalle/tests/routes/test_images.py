import unittest
import os.path
import json
import tempfile
import hashlib
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth
from tempfile import mkdtemp

from Hinkskalle.models import Image, Tag
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.tests.models.test_Container import _create_container

def _prepare_img_data(data=b"Hello Dorian!"):
    img_data=data
    m = hashlib.sha256()
    m.update(img_data)
    return img_data, f"sha256.{m.hexdigest()}"

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
  
  def test_get_default(self):
    image, _, _, entity = _create_image()
    entity.name='default'
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

  def test_pull(self):
    image, container, _, _ = _create_image()
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
    container.reload()
    self.assertEqual(container.downloadCount, 1)
    ret.close() # avoid unclosed filehandle warning

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    container.reload()
    self.assertEqual(container.downloadCount, 2)
    ret.close() # avoid unclosed filehandle warning

    tmpf.close()

  def test_pull_default_entity(self):
    image, _, _, entity = _create_image()
    image.uploaded=True
    latest_tag = Tag(name='latest', image_ref=image)
    latest_tag.save()

    entity.name='default'
    entity.save()

    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(b"Hello default Entity!")
    tmpf.flush()
    image.location=tmpf.name
    image.save()

    ret = self.client.get(f"/v1/imagefile//{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close()

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile///{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close() # avoid unclosed filehandle warning
    tmpf.close()
  
  def test_push_noauth(self):
    ret = self.client.post("/v1/imagefile/whatever")
    self.assertEqual(ret.status_code, 401)

  def test_push(self):
    image, container, _, _ = _create_image()
    self.app.config['IMAGE_PATH']=mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    image.save()

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    # no more auto-tagging
    read_image = Image.objects.get(id=image.id)
    self.assertTrue(read_image.uploaded)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

  def test_push_invalid_hash(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=mkdtemp()

    img_data=b"Hello Dorian!"

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 422)
  
  def test_push_create_dir(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=os.path.join(mkdtemp(), 'oink', 'oink')
    img_data, digest = _prepare_img_data()
    image.hash=digest
    image.save()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
  
  def test_push_overwrite(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=os.path.join(mkdtemp(), 'oink', 'oink')
    image.uploaded=True
    image.location='/gru/nz'

    img_data, digest = _prepare_img_data()
    image.hash=digest
    image.save()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    read_image = Image.objects.get(id=image.id)
    self.assertNotEqual(read_image.location, '/gru/nz')

  def test_push_user(self):
    image, container, coll, entity = _create_image()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.hase'
    coll.save()
    container.createdBy = 'test.hase'
    container.save()

    self.app.config['IMAGE_PATH']=mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    image.save()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)

  def test_push_user_other(self):
    image, container, coll, entity = _create_image()
    entity.createdBy = 'test.hase'
    entity.save()
    coll.createdBy = 'test.hase'
    coll.save()
    container.createdBy = 'test.kuh'
    container.save()

    self.app.config['IMAGE_PATH']=mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    image.save()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 403)