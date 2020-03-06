import unittest
import os.path
import json
import tempfile
import hashlib
from Hinkskalle.tests.route_base import RouteBase, fake_auth, fake_admin_auth

from Hinkskalle.models import Image, Tag, Container
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle import db

def _prepare_img_data(data=b"Hello Dorian!"):
    img_data=data
    m = hashlib.sha256()
    m.update(img_data)
    return img_data, f"sha256.{m.hexdigest()}"

def _fake_img_file(image, data=b"Hello Dorian!"):
    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(data)
    tmpf.flush()
    image.location=tmpf.name
    image.uploaded=True
    db.session.commit()
    return tmpf


class TestImages(RouteBase):
  def test_pull(self):
    image, container, _, _ = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.commit()

    tmpf = _fake_img_file(image)

    ret = self.client.get(f"/v1/imagefile/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello Dorian!")
    db_container = Container.query.get(container.id)
    self.assertEqual(db_container.downloadCount, 1)
    db_image = Image.query.get(image.id)
    self.assertEqual(db_image.downloadCount, 1)
    self.assertEqual(db_image.containerDownloads(), 1)
    ret.close() # avoid unclosed filehandle warning

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)

    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.data, b"Hello Dorian!")
    db_container = Container.query.get(container.id)
    self.assertEqual(db_container.downloadCount, 2)
    db_image = Image.query.get(image.id)
    self.assertEqual(db_image.downloadCount, 2)
    self.assertEqual(db_image.containerDownloads(), 2)
    ret.close() # avoid unclosed filehandle warning

    tmpf.close()
  
  def test_pull_private(self):
    image, container, _, _ = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)
    container.private = True
    db.session.commit()

    tmpf = _fake_img_file(image)

    ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 403)

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
      self.assertEqual(ret.status_code, 308)
      ret = self.client.get(ret.headers.get('Location'))
      self.assertEqual(ret.status_code, 403)

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
      self.assertEqual(ret.status_code, 308)
      ret = self.client.get(ret.headers.get('Location'))
      self.assertEqual(ret.status_code, 200)
    ret.close()
    
    tmpf.close()
  
  def test_pull_private_own(self):
    image, container, _, _ = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)
    container.private = True
    container.createdBy = 'test.hase'
    db.session.commit()

    tmpf = _fake_img_file(image)
    
    with fake_auth(self.app):
      ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
      self.assertEqual(ret.status_code, 308)
      ret = self.client.get(ret.headers.get('Location'))
      self.assertEqual(ret.status_code, 200)
    ret.close()
    
    tmpf.close()

  def test_pull_default_entity(self):
    image, _, _, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    entity.name='default'
    db.session.commit()

    tmpf = _fake_img_file(image, b"Hello default Entity!")

    ret = self.client.get(f"/v1/imagefile/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close()

    ret = self.client.get(f"/v1/imagefile//{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close()

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile///{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get("Location"))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get("Location"))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Entity!")
    ret.close() # avoid unclosed filehandle warning
    tmpf.close()

  def test_pull_default_collection(self):
    image, _, collection, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    collection.name='default'
    db.session.commit()

    tmpf = _fake_img_file(image, b"Hello default Collection!")

    ret = self.client.get(f"/v1/imagefile/{image.entityName()}//{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile/{image.entityName()}/default/{image.containerName()}:{latest_tag.name}$")

    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close()

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile//{image.entityName()}//{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile//{image.entityName()}/default/{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))

    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close() # avoid unclosed filehandle warning
    tmpf.close()

  def test_pull_default_entity_default_collection(self):
    image, _, collection, entity = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    collection.name='default'
    entity.name='default'
    db.session.commit()

    tmpf = _fake_img_file(image, b"Hello default Collection!")

    ret = self.client.get(f"/v1/imagefile///{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile//default/{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))

    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close()

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile////{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile//default//{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile//default/default/{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close() # avoid unclosed filehandle warning

    ret = self.client.get(f"/v1/imagefile//{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/imagefile/{image.containerName()}:{latest_tag.name}$")

    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close() # avoid unclosed filehandle warning

    ret = self.client.get(f"/v1/imagefile/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close() # avoid unclosed filehandle warning
    tmpf.close()
  
  def test_push_noauth(self):
    ret = self.client.post("/v1/imagefile/whatever")
    self.assertEqual(ret.status_code, 401)

  def test_push(self):
    image, container, _, _ = _create_image()
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()
    image_id = image.id
    container_id = container.id

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    # no more auto-tagging
    read_image = Image.query.get(image_id)
    self.assertTrue(read_image.uploaded)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.imageTags(), { 'latest': read_image.id }, 'latest tag updated')

  def test_push_readonly(self):
    image, container, _, _ = _create_image()
    container.readOnly = True
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 406)

  def test_push_invalid_hash(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()

    img_data=b"Hello Dorian!"

    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 422)
  
  def test_push_create_dir(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=os.path.join(tempfile.mkdtemp(), 'oink', 'oink')
    img_data, digest = _prepare_img_data()
    image.hash=digest
    db.session.commit()
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
  
  def test_push_overwrite(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=os.path.join(tempfile.mkdtemp(), 'oink', 'oink')
    image.uploaded=True
    image.location='/gru/nz'

    img_data, digest = _prepare_img_data()
    image.hash=digest
    db.session.commit()
    image_id = image.id
    with fake_admin_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    read_image = Image.query.get(image_id)
    self.assertNotEqual(read_image.location, '/gru/nz')

  def test_push_user(self):
    image, container, coll, entity = _create_image()
    entity.createdBy = 'test.hase'
    coll.createdBy = 'test.hase'
    container.createdBy = 'test.hase'
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)

  def test_push_user_other(self):
    image, container, coll, entity = _create_image()
    entity.createdBy = 'test.hase'
    coll.createdBy = 'test.hase'
    container.createdBy = 'test.kuh'
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with fake_auth(self.app):
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 403)