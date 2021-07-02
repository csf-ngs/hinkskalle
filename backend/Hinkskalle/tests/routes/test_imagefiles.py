from typing import Tuple
import unittest
import os.path
import json
import tempfile
import hashlib

from flask.globals import current_app
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.models import Image, Tag, Container
from Hinkskalle.models.Entity import Entity
from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle import db

def _prepare_img_data(data=b"Hello Dorian!") -> Tuple[bytes, str]:
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


class TestImagefiles(RouteBase):

  def test_make_filename(self):
    self.app.config['IMAGE_PATH_HASH_LEVEL']=2
    image = _create_image(hash='sha256.oink')[0]
    from Hinkskalle.routes.imagefiles import _make_filename
    fn = _make_filename(image)
    self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}_imgs/o/i/sha256.oink.sif")

    self.app.config['IMAGE_PATH_HASH_LEVEL']=99
    fn = _make_filename(image)
    self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}_imgs/o/i/n/k/sha256.oink.sif")

    self.app.config['IMAGE_PATH_HASH_LEVEL']=0
    fn = _make_filename(image)
    self.assertEqual(fn, f"{self.app.config.get('IMAGE_PATH')}_imgs/sha256.oink.sif")


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
  
  def test_pull_arch(self):
    image1, container, _, _ = _create_image()
    image1_tag = Tag(name='v1', image_ref=image1, arch='c64')
    image1.arch='c64'

    image2 = Image(hash='sha256.oink2', container_ref=container, arch='amiga')
    image2_tag = Tag(name='v1', image_ref=image2, arch='amiga')
    db.session.add(image1_tag)
    db.session.add(image2_tag)
    db.session.commit()

    tmpf1 = _fake_img_file(image1, data=b"oink c64/v1")
    tmpf2 = _fake_img_file(image2, data=b"oink amiga/v1")

    ret = self.client.get(f"/v1/imagefile/{image1.entityName()}/{image1.collectionName()}/{image1.containerName()}:{image1_tag.name}?arch=c64")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"oink c64/v1")
    ret.close()
  
  def test_pull_no_sif(self):
    image = _create_image(media_type='something')[0]
    image_tag = Tag(name='v1', image_ref=image, arch='c64')
    image.arch='c64'
    db.session.add(image_tag)
    tmpf1 = _fake_img_file(image, data=b"oink c64/v1")

    ret = self.client.get(f"/v1/imagefile/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{image_tag.name}")
    self.assertEqual(ret.status_code, 406)


  def test_pull_private_noauth(self):
    image, container, _, _ = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)
    container.private = True
    db.session.commit()

    tmpf = _fake_img_file(image)
    ret = self.client.get(f"/v1/imagefile/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 403)

  
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

    with self.fake_auth():
      ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
      self.assertEqual(ret.status_code, 308)
      ret = self.client.get(ret.headers.get('Location'))
      self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
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
    container.owner=self.user
    db.session.commit()

    tmpf = _fake_img_file(image)
    
    with self.fake_auth():
      ret = self.client.get(f"/v1/imagefile//{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
      self.assertEqual(ret.status_code, 308)
      ret = self.client.get(ret.headers.get('Location'))
      self.assertEqual(ret.status_code, 200)
    ret.close()
    
    tmpf.close()

  def test_pull_private_denied(self):
    image, container, _, _ = _create_image()
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)
    container.private = True
    container.owner=self.other_user
    db.session.commit()

    tmpf = _fake_img_file(image)
    
    with self.fake_auth():
      ret = self.client.get(f"/v1/imagefile/{image.entityName()}/{image.collectionName()}/{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 403)
    

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
    self.assertRegex(ret.headers.get('Location', ''), rf"/v1/imagefile//{image.entityName()}/default/{image.containerName()}:{latest_tag.name}$")
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
    self.assertRegex(ret.headers.get('Location',''), rf"/v1/imagefile//default/{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))

    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close()

    # singularity requests with double slash
    ret = self.client.get(f"/v1/imagefile////{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', ''), rf"/v1/imagefile//default//{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', ''), rf"/v1/imagefile//default/default/{image.containerName()}:{latest_tag.name}$")
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308)
    ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b"Hello default Collection!")
    ret.close() # avoid unclosed filehandle warning

    ret = self.client.get(f"/v1/imagefile//{image.containerName()}:{latest_tag.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', ''), rf"/v1/imagefile/{image.containerName()}:{latest_tag.name}$")

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

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    # no more auto-tagging
    read_image = Image.query.get(image_id)
    self.assertTrue(read_image.uploaded)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.imageTags(),
      { 'latest': str(read_image.id) }, 'latest tag updated')
    self.assertDictEqual(db_container.archImageTags(),
      { 'amd64': { 'latest': str(read_image.id) }}, 'arch image tag updated'
    )
    db_image = Image.query.get(image_id)
    self.assertEqual(db_image.arch, 'amd64')
  
  def test_push_quota(self):
    image, container, _, entity = _create_image()
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()
    entity_id = entity.id

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, len(img_data))

  def test_push_quota_check(self):
    image, _, _, entity = _create_image()
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    entity.quota = len(img_data)-1
    db.session.commit()
    image_id = image.id
    entity_id = entity.id

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 413)
    image = Image.query.get(image_id)
    self.assertFalse(image.uploaded)


  def test_push_readonly(self):
    image, container, _, _ = _create_image()
    container.readOnly = True
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 406)

  def test_push_invalid_hash(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()

    img_data=b"Hello Dorian!"

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 422)
  
  def test_push_create_dir(self):
    image = _create_image()[0]
    self.app.config['IMAGE_PATH']=os.path.join(tempfile.mkdtemp(), 'oink', 'oink')
    img_data, digest = _prepare_img_data()
    image.hash=digest
    db.session.commit()
    with self.fake_admin_auth():
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
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)
    read_image = Image.query.get(image_id)
    self.assertNotEqual(read_image.location, '/gru/nz')

  def test_push_user(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 200)

  def test_push_user_other(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.other_user
    db.session.commit()

    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", data=img_data)
    self.assertEqual(ret.status_code, 403)
