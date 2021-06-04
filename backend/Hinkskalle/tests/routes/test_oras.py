from Hinkskalle.models.Image import Image
import tempfile
from Hinkskalle.models.Container import Container
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
import datetime
import os.path
import json

from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle import db
from Hinkskalle.models import Tag, Manifest, ImageUploadUrl, UploadStates, UploadTypes
from Hinkskalle.tests.models.test_Image import _create_image
from .test_imagefiles import _fake_img_file, _prepare_img_data

class TestOras(RouteBase):

  def test_manifest(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertIsNotNone(digest)

    manifest = Manifest.query.filter(Manifest.hash == digest.replace('sha256:', '')).first()
    self.assertIsNotNone(manifest)
    self.assertDictEqual(ret.get_json().get('layers')[0], {
      'mediaType': 'application/vnd.sylabs.sif.layer.v1.sif',
      'digest': f"sha256:{image.hash.replace('sha256.', '')}",
      'size': None,
      'annotations': {
        'org.opencontainers.image.title': image.containerName(),
      }
    })

  def test_manifest_private(self):
    image, container, collection, entity = _create_image(postfix='1')
    container.private=True
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 403)

    image, container, collection, entity = _create_image(postfix='2')
    collection.private=True
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 403)
  
  def test_manifest_tag_not_found(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/earliest")
    self.assertEqual(ret.status_code, 404)

  
  def test_manifest_default(self):
    image, container, collection, entity = _create_image(postfix='1')
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    ret = self.client.get(f"/v2/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 404)

    entity.name='default'
    db.session.commit()

    ret = self.client.get(f"/v2/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)

    ret = self.client.get(f"/v2/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 404)

    collection.name='default'
    db.session.commit()
    ret = self.client.get(f"/v2/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)



  def test_manifest_double(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertIsNotNone(digest)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    next_digest = ret.headers.get('Docker-Content-Digest')
    self.assertEqual(digest, next_digest)

  def test_manifest_double_different_tag(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    other_tag = Tag(name='other', image_ref=image)
    db.session.add(latest_tag)
    db.session.add(other_tag)

    db.session.commit()

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/latest")
    self.assertEqual(ret.status_code, 200)
    digest = ret.headers.get('Docker-Content-Digest')
    self.assertIsNotNone(digest)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/other")
    self.assertEqual(ret.status_code, 200)
    next_digest = ret.headers.get('Docker-Content-Digest')
    self.assertEqual(digest, next_digest)
  
  def test_manifest_refetch(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    manifest = Manifest(content='{"oi": "nk"}')
    latest_tag.manifest_ref=manifest

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}")
    self.assertEqual(ret.status_code, 200)

    self.assertDictEqual(ret.get_json(), {'oi': 'nk'})

  def test_manifest_hash_notfound(self):
    image = _create_image()[0]
    latest_tag = Tag(name='latest', image_ref=image)
    db.session.add(latest_tag)

    manifest = Manifest(content='{"oi": "nk"}')
    latest_tag.manifest_ref=manifest

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/manifests/sha256:{manifest.hash}oink")
    self.assertEqual(ret.status_code, 404)

  def test_blob(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.data, b'Hello Dorian!')

  def test_blob_unsupported(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha512:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 400)

  def test_blob_not_found(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}oink/{image.collectionName()}/{image.containerName()}/blobs/sha256:{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 404)

  def test_blob_hash_not_found(self):
    image = _create_image()[0]
    file = _fake_img_file(image)

    ret = self.client.get(f"/v2/{image.entityName()}/{image.collectionName()}/{image.containerName()}/blobs/sha256:oink{image.hash.replace('sha256.', '')}")
    self.assertEqual(ret.status_code, 404)
  
  def test_push_monolith_get_session(self):
    """https://github.com/opencontainers/distribution-spec/blob/main/spec.md#post-then-put"""    

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/test/hase/blobs/uploads/")
    self.assertEqual(ret.status_code, 202)
    self.assertIsNotNone(ret.headers.get('location'))

    upload_id = ret.headers.get('location').split('/')[-1]

    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==upload_id).first()
    self.assertIsNotNone(db_upload)
    self.assertEqual(db_upload.state, UploadStates.initialized)
    self.assertEqual(db_upload.type, UploadTypes.single)
    self.assertTrue(abs(db_upload.expiresAt - (datetime.datetime.now()+datetime.timedelta(minutes=5))) < datetime.timedelta(minutes=1))
    self.assertTrue(os.path.exists(db_upload.path))
    self.assertFalse(db_upload.image_ref.uploaded)

    # check autovivification of container path
    entity: Entity = Entity.query.filter(Entity.name=='default').first()
    self.assertIsNotNone(entity)
    collection = entity.collections_ref.filter(Collection.name=='test').first()
    self.assertIsNotNone(collection)
    container = collection.containers_ref.filter(Container.name=='hase').first()
    self.assertIsNotNone(container)

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
  
  def test_push_monolith_do(self):
    image, container, collection, entity = _create_image()
    image_id = image.id
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      state = UploadStates.initialized,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    digest = digest.replace('sha256.', 'sha256:')
    ret = self.client.put(f"/v2/__uploads/{upload.id}?digest={digest}", data=img_data, content_type='application/octet-stream')
    self.assertEqual(ret.status_code, 201)
    self.assertRegexpMatches(ret.headers.get('location'), rf'/{entity.name}/{collection.name}/{container.name}/blobs/{digest}')
    self.assertIsNotNone(ret.headers.get('location'))

    upload_digest = ret.headers.get('Docker-Content-Digest', '')
    self.assertEqual(upload_digest, digest)

    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.completed)

    db_image: Image = Image.query.get(image_id)
    self.assertTrue(db_image.uploaded)
    self.assertEqual(db_image.size, len(img_data))
    with open(db_image.location, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)
    
  
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

  def test_push_manifest_existing(self):
    image, container, collection, entity = _create_image()
    tag1 = Tag(name='v2', image_ref=image)
    manifest = Manifest(content={'oi': 'nk'})
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

    manifest = Manifest(content=test_manifest_text)
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

    manifest = Manifest(content=test_manifest_text)
    tag1.manifest_ref=manifest
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.add(manifest)

    manifest2 = Manifest(content={'oi': 'nk'})
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
  
  def test_push_manifest_create_tag(self):
    image, container, collection, entity = _create_image()
    test_manifest = {
      "schemaVersion": 2,
      "layers": [
        { 'digest': image.hash.replace('sha256.', 'sha256:') }
      ],
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
    self.assertEqual(ret.status_code, 404)

    test_manifest = {
      "schemaVersion": 2,
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)

  def test_push_manifest_layer_not_found(self):
    image, container, collection, entity = _create_image()
    test_manifest = {
      "schemaVersion": 2,
      "layers": [
        { 'digest': image.hash.replace('sha256.', 'sha256:')+'oink' }
      ],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)

    tag1 = Tag(name='v2', image_ref=image)
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
      "layers": [
        { 'digest': image.hash.replace('sha256.', 'sha256:') }
      ],
    }
    with self.fake_admin_auth():
      ret = self.client.put(f'/v2/{entity.name}/{collection.name}/{container.name}oink/manifests/v2', json=test_manifest)
    self.assertEqual(ret.status_code, 404)