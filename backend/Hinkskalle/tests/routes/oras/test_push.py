from Hinkskalle.models.Image import Image
from unittest import mock
import tempfile
from Hinkskalle.models.Container import Container
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models.Tag import Tag
import datetime
import os.path
import os
import json

from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests._util import _create_image, _create_container, _prepare_img_data

from Hinkskalle import db
from Hinkskalle.models import Manifest, ImageUploadUrl, UploadStates, UploadTypes


class TestOrasPush(RouteBase):

  def test_push_monolith_no_auth(self):
    ret = self.client.post(f"/v2/test/hase/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 401)

  def test_push_monolith_get_session(self):
    """https://github.com/opencontainers/distribution-spec/blob/main/spec.md#post-then-put"""    

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/test/hase/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 202)
    self.assertIsNotNone(ret.headers.get('location'))

    upload_id = ret.headers.get('location').split('/')[-1]

    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==upload_id).first()
    self.assertIsNotNone(db_upload)
    self.assertEqual(db_upload.state, UploadStates.initialized)
    self.assertEqual(db_upload.type, UploadTypes.undetermined)
    self.assertTrue(abs(db_upload.expiresAt - (datetime.datetime.now()+datetime.timedelta(minutes=5))) < datetime.timedelta(minutes=1))
    self.assertTrue(os.path.exists(db_upload.path))
    self.assertEqual(db_upload.image_ref.uploadState, UploadStates.initialized)
    self.assertEqual(db_upload.createdBy, self.admin_username)
    self.assertEqual(db_upload.image_ref.media_type, 'unknown')

    self.assertEqual(db_upload.image_ref.createdBy, self.admin_username)

    # check autovivification of container path
    entity: Entity = Entity.query.filter(Entity.name=='default').first()
    self.assertIsNotNone(entity)
    self.assertEqual(entity.createdBy, self.admin_username)
    collection = entity.collections_ref.filter(Collection.name=='test').first()
    self.assertIsNotNone(collection)
    self.assertEqual(collection.createdBy, self.admin_username)
    container = collection.containers_ref.filter(Container.name=='hase').first()
    self.assertIsNotNone(container)
    self.assertEqual(container.createdBy, self.admin_username)
  
  def test_push_monolith_behalf(self):
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{self.username}/hase/grase/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)

    entity = Entity.query.filter(Entity.name==self.username).first()
    self.assertEqual(entity.owner.username, self.username)
    collection = entity.collections_ref.filter(Collection.name=='hase').first()
    self.assertEqual(collection.owner.username, self.username)
    container = collection.containers_ref.filter(Container.name=='grase').first()
    self.assertEqual(container.owner.username, self.username)

  def test_push_monolith_behalf_existing(self):
    entity = Entity(name='schlumpf.hase', owner=self.user)
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/schlumpf.hase/hase/grase/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)

    entity = Entity.query.filter(Entity.name=='schlumpf.hase').first()
    self.assertEqual(entity.owner.username, self.username)
    collection = entity.collections_ref.filter(Collection.name=='hase').first()
    self.assertEqual(collection.owner.username, self.username)
    container = collection.containers_ref.filter(Container.name=='grase').first()
    self.assertEqual(container.owner.username, self.username)
  
  def test_push_monolith_create_user(self):
    with self.fake_auth():
      ret = self.client.post(f"/v2/test/hase/stall/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 403)
    with self.fake_auth():
      ret = self.client.post(f"/v2/{self.username}/hase/stall/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 202)

    entity = Entity(name='test', owner=self.other_user)
    db.session.add(entity)
    with self.fake_auth():
      ret = self.client.post(f"/v2/{entity.name}/hase/stall/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 403)
    self.assertIsNone(Collection.query.filter(Collection.name=='hase', Collection.entity_id==entity.id).first())

    _, _, collection, entity = _create_image()
    entity.owner = self.other_user
    collection.owner = self.other_user

    db.session.commit()
    with self.fake_auth():
      ret = self.client.post(f"/v2/{entity.name}/{collection.name}/stall/blobs/uploads/", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 403)
    self.assertIsNone(Container.query.filter(Container.name=='stall', Container.collection_id==collection.id).first())
    
  def test_push_monolith_create_set_expiration(self): 
    exp = '2030-08-05T23:47:45.480581'
    with self.fake_auth():
      ret = self.client.post(f"/v2/{self.username}/hase/stall/blobs/uploads/?expiresAt={exp}", headers={'Content-Length': 0 })
    print(ret.get_json())
    self.assertEqual(ret.status_code, 202)
    db_container = Container.query.filter(Container.name=='stall').one()
    db_image = db_container.images_ref.first()
    self.assertEquals(db_image.expiresAt, datetime.datetime.fromisoformat(exp))

  def test_push_monolith_create_set_private(self): 
    with self.fake_auth():
      ret = self.client.post(f"/v2/{self.username}/hase/stall/blobs/uploads/?private=true", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 202)
    db_collection = Collection.query.filter(Collection.name=='hase').one()
    self.assertTrue(db_collection.private)
    db_container = Container.query.filter(Container.name=='stall').one()
    self.assertTrue(db_container.private)

  def test_push_monolith_create_set_private_existing(self): 
    container, collection, entity = _create_container()
    entity.name = self.username
    entity.owner = self.user
    collection.owner = self.user
    container.owner = self.user
    db.session.commit()
    collection_id = collection.id
    container_id = container.id
    with self.fake_auth():
      ret = self.client.post(f"/v2/{self.username}/{collection.name}/{container.name}/blobs/uploads/?private=true", headers={'Content-Length': 0 })
    self.assertEqual(ret.status_code, 202)
    db_collection = Collection.query.get(collection_id)
    self.assertFalse(db_collection.private)
    db_container = Container.query.get(container_id)
    self.assertTrue(db_container.private)


  def test_push_monolith_create_private(self):
    image = _create_image('1')[0]
    image.container_ref.collection_ref.private=True
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/fintitax1/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_container = Container.query.filter(Container.name=='fintitax1').one()
    self.assertTrue(db_container.private)

    image = _create_image('2')[0]
    image.container_ref.collection_ref.private=False
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/fintitax2/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_container = Container.query.filter(Container.name=='fintitax2').one()
    self.assertFalse(db_container.private)

  def test_push_monolith_create_private_collection(self):
    image, container, collection, entity = _create_image('1')
    entity.defaultPrivate = True
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/fintitax-coll1/fintitax-cont1/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_collection = Collection.query.filter(Collection.name=='fintitax-coll1').one()
    self.assertTrue(db_collection.private)
    db_container = Container.query.filter(Container.name=='fintitax-cont1').one()
    self.assertTrue(db_container.private)

    image, container, collection, entity = _create_image('2')
    entity.defaultPrivate = False
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/fintitax-coll2/fintitax-cont2/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_collection = Collection.query.filter(Collection.name=='fintitax-coll2').one()
    self.assertFalse(db_collection.private)
    db_container = Container.query.filter(Container.name=='fintitax-cont2').one()
    self.assertFalse(db_container.private)

   
  def test_push_monolith_mount(self):
    image1 = _create_image(postfix='1')[0]
    image1_id = image1.id
    image2 = _create_image(postfix='2', hash='sha256.muh')[0]

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image1.entityName}/{image1.collectionName}/{image1.containerName}/blobs/uploads/?mount={image2.hash.replace('sha256.', 'sha256:')}&from={image2.entityName}/{image2.collectionName}/{image2.containerName}")
    self.assertEqual(ret.status_code, 201)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertEqual(digest.replace('sha256:', 'sha256.'), 'sha256.muh')
    image1 = Image.query.get(image1_id)
    self.assertRegexpMatches(ret.headers.get('location', ''), rf'/{image1.entityName}/{image1.collectionName}/{image1.containerName}/blobs/{digest}')
    new_image = Image.query.filter(Image.hash=='sha256.muh', Image.container_ref==image1.container_ref).one()

  def test_push_monolith_mount_not_found(self):
    image1 = _create_image(postfix='1')[0]
    image1_id = image1.id
    image2 = _create_image(postfix='2', hash='sha256.muh')[0]

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image1.entityName}/{image1.collectionName}/{image1.containerName}/blobs/uploads/?mount={image2.hash.replace('sha256.', 'sha256:')}&from={image2.entityName}/{image2.collectionName}oink/{image2.containerName}")
    self.assertEqual(ret.status_code, 404)

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image1.entityName}/{image1.collectionName}/{image1.containerName}/blobs/uploads/?mount={image2.hash.replace('sha256.', 'sha256:')}oink&from={image2.entityName}/{image2.collectionName}/{image2.containerName}")
    self.assertEqual(ret.status_code, 404)

  def test_push_monolith_get_session_existing(self):
    _, container, collection, entity = _create_image(postfix='1')
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{entity.name}/{collection.name}/{container.name}/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)

    _, container, collection, entity = _create_image(postfix='2')
    entity_id = entity.id
    coll_name = collection.name
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{entity.name}/{collection.name}oink/{container.name}/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_coll = Collection.query.filter(Collection.name==f"{coll_name}oink", Collection.entity_id==entity_id).first()
    self.assertIsNotNone(db_coll)

    _, container, collection, entity = _create_image(postfix='3')
    coll_id = collection.id
    container_name = container.name
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{entity.name}/{collection.name}/{container.name}oink/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    db_container = Container.query.filter(Container.name==f"{container_name}oink", Container.collection_id==coll_id).first()
    self.assertIsNotNone(db_container)
  
  def test_push_monolith_get_session_user(self):
    _, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/{entity.name}/{coll.name}/{container.name}/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)

  def test_push_monolith_get_session_user_denied(self):
    _, container, coll, entity = _create_image()
    entity.owner=self.other_user
    coll.owner=self.other_user
    container.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/{entity.name}/{coll.name}/{container.name}/blobs/uploads/")
    self.assertEqual(ret.status_code, 403)
  
  def test_push_monolith_get_session_readonly(self):
    image = _create_image()[0]
    image.container_ref.readOnly = True
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/")
    self.assertEqual(ret.status_code, 403)

  def test_push_monolith_do(self):
    image, container, collection, entity = _create_image()
    image_id = image.id
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    digest = digest.replace('sha256.', 'sha256:')
    # just make sure that we use the same filename generation method as library push
    with mock.patch('Hinkskalle.routes.imagefiles._make_filename') as mock_make_fn:
      outpath = os.path.join(os.path.abspath(self.app.config['IMAGE_PATH']), '_imgs', digest)
      os.makedirs(os.path.dirname(outpath), exist_ok=True)
      mock_make_fn.return_value=outpath

      ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)
    self.assertRegexpMatches(ret.headers.get('location', ''), rf'/{entity.name}/{collection.name}/{container.name}/blobs/{digest}')
    self.assertIsNotNone(ret.headers.get('location'))
    mock_make_fn.assert_called()

    upload_digest = ret.headers.get('Docker-Content-Digest', '')
    self.assertEqual(upload_digest, digest)

    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.type, UploadTypes.single)
    self.assertEqual(read_upload.state, UploadStates.completed)

    db_image: Image = Image.query.get(image_id)
    self.assertEqual(db_image.uploadState, UploadStates.completed)
    self.assertTrue(db_image.hide)
    self.assertEqual(db_image.size, len(img_data))
    with open(db_image.location, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)

  def test_push_monolith_do_quota(self):
    image, container, collection, entity = _create_image()
    entity_id = entity.id
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
    )
    db.session.add(upload)
    db.session.commit()

    digest = digest.replace('sha256.', 'sha256:')
    ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)

    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, len(img_data))

  def test_push_monolith_do_quota_check(self):
    image, container, collection, entity = _create_image()
    img_data, digest = _prepare_img_data()
    image_id = image.id
    entity.quota = len(img_data)-1

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    digest = digest.replace('sha256.', 'sha256:')
    ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 413)
    upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(upload.state, UploadStates.failed)
    image = Image.query.get(image_id)
    self.assertEqual(image.uploadState, UploadStates.failed)


  def test_push_monolith_checksum_mismatch(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    digest = digest.replace('sha256.', 'sha256:')
    ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}oink", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 400)

  def test_push_monolith_duplicate(self):
    image, container, _, _ = _create_image()
    img_data, digest = _prepare_img_data()

    image2 = Image(container_ref=container, hash=digest)
    db.session.add(image2)

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    digest = digest.replace('sha256.', 'sha256:')
    ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)

    db_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(db_upload.image_id, image2.id)
    
  def test_push_single_post(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)
    self.assertEqual(ret.headers.get('Docker-Content-Digest'), digest)

    db_image: Image = Image.query.filter(Image.hash==digest.replace('sha256:', 'sha256.')).one()
    self.assertEqual(db_image.uploadState, UploadStates.completed)
    self.assertTrue(db_image.hide)
    self.assertEqual(db_image.size, len(img_data))
    with open(db_image.location, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)
    
    upload = ImageUploadUrl.query.filter(ImageUploadUrl.image_id==db_image.id).first()
    self.assertEqual(upload.type, UploadTypes.single)
    self.assertEqual(upload.state, UploadStates.completed)

  def test_push_single_post_stage(self):
    self.app.config['STAGING_PATH']=tempfile.mkdtemp()
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()
    with open(os.path.join(self.app.config['STAGING_PATH'], digest), 'w') as outfh:
      outfh.write(img_data.decode('utf8'))

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}&staged=1", content_type='application/octet-stream')
    print(ret.get_json())
    self.assertEqual(ret.status_code, 201)
    self.assertEqual(ret.headers.get('Docker-Content-Digest'), digest.replace('sha256.', 'sha256:'))
    db_image: Image = Image.query.filter(Image.hash==digest.replace('sha256:', 'sha256.')).one()
    self.assertEqual(db_image.uploadState, UploadStates.completed)

    with open(db_image.location, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)

    upload = ImageUploadUrl.query.filter(ImageUploadUrl.image_id==db_image.id).first()
    self.assertEqual(upload.type, UploadTypes.single)
    self.assertEqual(upload.state, UploadStates.completed)

  def test_push_single_post_stage_invalid(self):
    self.app.config['STAGING_PATH']=tempfile.mkdtemp()
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()
    with open(os.path.join(self.app.config['STAGING_PATH'], f"oink{digest}"), 'w') as outfh:
      outfh.write(img_data.decode('utf8'))

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}&staged=1", content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 400)

  def test_push_single_post_stage_user(self):
    self.app.config['STAGING_PATH']=tempfile.mkdtemp()
    image, container, collection, entity = _create_image()
    entity.owner = self.user
    collection.owner = self.user
    container.owner = self.user
    img_data, digest = _prepare_img_data()
    with open(os.path.join(self.app.config['STAGING_PATH'], digest), 'w') as outfh:
      outfh.write(img_data.decode('utf8'))

    with self.fake_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}&staged=1", content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 403)

  def test_push_single_post_quota(self):
    image, _, _, entity = _create_image()
    entity_id = entity.id
    img_data, digest = _prepare_img_data()
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)
    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, len(img_data))

  def test_push_single_post_quota_check(self):
    image, _, _, entity = _create_image()
    image_container_id = image.id
    img_data, digest = _prepare_img_data()
    entity.quota = len(img_data)-1
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 413)

  def test_push_single_post_user(self):
    image, container, collection, entity = _create_image()
    entity.owner = self.user
    collection.owner = self.user
    container.owner = self.user
    img_data, digest = _prepare_img_data()
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)

    db_image: Image = Image.query.filter(Image.hash==digest.replace('sha256:', 'sha256.')).one()
    self.assertEqual(db_image.createdBy, self.username)

  def test_push_single_post_user_denied(self):
    image, container, collection, entity = _create_image()
    entity.owner = self.other_user
    collection.owner = self.other_user
    container.owner = self.other_user
    img_data, digest = _prepare_img_data()
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 403)

  def test_push_single_post_no_digest(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()
    digest = digest.replace('sha256.', 'sha256:')

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{image.entityName}/{image.collectionName}/{image.containerName}/blobs/uploads/", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 400)

  def test_push_manifest_noauth(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 401)
  
  def test_push_manifest(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)
    location: str = ret.headers.get('location', '')
    self.assertRegex(location, rf"/v2/{entity.name}/{collection.name}/{container.name}/manifests/")
    hash = location.split('/')[-1].replace('sha256:', '')
    db_manifest = Manifest.query.filter(Manifest.hash==hash).first()
    self.assertIsNotNone(db_manifest)
    self.assertDictEqual(db_manifest.content_json, test_manifest)

    digest: str = ret.headers.get('Docker-Content-Digest', '')
    self.assertEqual(digest, f"sha256:{hash}")
  
  
  def test_push_manifest_readonly(self):
    image = _create_image()[0]
    image.container_ref.readOnly = True
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{image.entityName}/{image.collectionName}/{image.containerName}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 403)


  def test_push_manifest_user(self):
    image, container, collection, entity = _create_image()
    container.owner = self.user
    collection.owner = self.user
    entity.owner = self.user
    tag1 = Tag(name='v2', image_ref=image, owner=self.user)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

  def test_push_manifest_user_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='v2', image_ref=image, owner=self.user)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 403)

  def test_push_manifest_user_tag_denied(self):
    image, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user
    tag1 = Tag(name='v2', image_ref=image, owner=self.other_user)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 403)

  def test_push_manifest_existing(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content={'oi': 'nk'}, container_ref=container)
    tag1.manifest_ref=manifest
    db.session.add(tag1, manifest)
    db.session.commit()
    manifest_id = manifest.id

    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)
    db_manifest = Manifest.query.get(manifest_id)
    self.assertDictEqual(db_manifest.content_json, test_manifest)

  def test_push_manifest_existing_same_content(self):
    image, container, collection, entity = _create_image()
    test_manifest = { "schemaVersion": 2 }
    manifest = Manifest(
      content = test_manifest,
      container_ref=container,
    )
    tag1 = Tag(name='v2', image_ref=image, manifest_ref=manifest)
    db.session.add(tag1)
    db.session.add(manifest)
    db.session.commit()
    manifest_id = manifest.id
    manifest_hash = manifest.hash

    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

    db_manifest = Manifest.query.get(manifest_id)
    self.assertEqual(db_manifest.hash, manifest_hash)





  def test_push_manifest_existing_other_tag(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    tag2 = Tag(name='other', image_ref=image)

    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    test_manifest_text = json.dumps(test_manifest)

    manifest = Manifest(content=test_manifest_text, container_ref=container)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(manifest)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/other', data=test_manifest_text)
    self.assertEqual(ret.status_code, 201)

    digest: str = ret.headers.get('Docker-Content-Digest', '')
    db_manifest = Manifest.query.filter(Manifest.hash == digest.replace('sha256:', '')).one()
    self.assertCountEqual(
      [ t.name for t in db_manifest.tags ],
      [ 'v2', 'other' ]
    )

  def test_push_manifest_existing_other_tag_overwrite(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    tag2 = Tag(name='other', image_ref=image)

    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
      },
      "layers": [],
    }
    test_manifest_text = json.dumps(test_manifest)

    manifest = Manifest(content=test_manifest_text, container_ref=container)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(manifest)

    manifest2 = Manifest(content={'oi': 'nk'}, container_ref=container)
    tag2.manifest_ref=manifest2
    db.session.add(manifest2)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/other', data=test_manifest_text)
    self.assertEqual(ret.status_code, 201)

    digest: str = ret.headers.get('Docker-Content-Digest', '')
    db_manifest = Manifest.query.filter(Manifest.hash == digest.replace('sha256:', '')).one()
    self.assertCountEqual(
      [ t.name for t in db_manifest.tags ],
      [ 'v2', 'other' ]
    )
  
  def test_push_manifest_update_images(self):
    image, container, collection, entity = _create_image()
    config_image = Image(container_ref=container, hash='sha256.config', media_type='unknown')
    other_image = Image(container_ref=container, hash='sha256.other', media_type='unknown')
    db.session.add(config_image)
    db.session.add(other_image)
    db.session.commit()

    image_id = image.id
    config_image_id = config_image.id
    other_image_id = other_image.id

    test_manifest = {
      "schemaVersion": 2,
      "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": config_image.hash.replace('sha256.', 'sha256:')
      },
      "layers": [{ 
        'digest': image.hash.replace('sha256.', 'sha256:'),
        "mediaType": "application/vnd.sylabs.sif.layer.v1.sif",
      }, {
        'digest': other_image.hash.replace('sha256.', 'sha256:'),
        "mediaType": "something",
      }],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

    db_image = Image.query.get(image_id)
    self.assertEqual(db_image.media_type, "application/vnd.sylabs.sif.layer.v1.sif")
    self.assertFalse(db_image.hide)
    self.assertListEqual(db_image.tags, ['v2'])

    db_other_image = Image.query.get(other_image_id)
    self.assertEqual(db_other_image.media_type, "something")
    self.assertTrue(db_other_image.hide)
    self.assertListEqual(db_other_image.tags, [])

    db_config_image = Image.query.get(config_image_id)
    self.assertEqual(db_config_image.media_type, "application/vnd.oci.image.config.v1+json")
    self.assertTrue(db_config_image.hide)
    self.assertListEqual(db_config_image.tags, [])



  def test_push_manifest_create_tag(self):
    image, container, collection, entity = _create_image()
    test_manifest = {
      "schemaVersion": 2,
      "layers": [{ 
        'digest': image.hash.replace('sha256.', 'sha256:'), 
        "mediaType": "application/vnd.sylabs.sif.layer.v1.sif",
      }],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)
  
  def test_push_manifest_create_tag_need_layer(self):
    image, container, collection, entity = _create_image()
    test_manifest = {
      "schemaVersion": 2,
      "layers": [],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

    test_manifest = {
      "schemaVersion": 2,
      "layers": [
        { 'mediaType': 'oink' },
      ],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

    test_manifest = {
      "schemaVersion": 2,
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 201)

  def test_push_manifest_layer_not_found(self):
    image, container, collection, entity = _create_image()
    image_id = image.id
    test_manifest = {
      "schemaVersion": 2,
      "layers": [{ 
        'digest': image.hash.replace('sha256.', 'sha256:')+'oink',
        "mediaType": "application/vnd.sylabs.sif.layer.v1.sif",
      }],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)

    tag1 = Tag(name='v2', image_ref=Image.query.get(image_id))
    db.session.add(tag1)
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)

  def test_push_manifest_not_found(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    db.session.add(tag1)
    test_manifest = {
      "schemaVersion": 2,
      "layers": [{ 
        'digest': image.hash.replace('sha256.', 'sha256:'),
        "mediaType": "application/vnd.sylabs.sif.layer.v1.sif",
      }],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}oink/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)
  