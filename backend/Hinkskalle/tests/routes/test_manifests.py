from Hinkskalle import db

from ..route_base import RouteBase
from .._util import _fake_img_file, _create_image

import jwt
from datetime import datetime
from calendar import timegm

from Hinkskalle.models.Manifest import Manifest
from Hinkskalle.models.Image import Image

class TestManifests(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/containers/what/ev/er/manifests')
    self.assertEqual(ret.status_code, 401)
  
  def test_list(self):
    image1 = _create_image(postfix='eins')[0]
    image2 = _create_image(hash='sha256.muh', postfix='zwei')[0]
    image2.container_ref = image1.container_ref

    mani1 = Manifest(content={'what': 'ever'}, container_ref=image1.container_ref)
    mani2 = Manifest(content={'not': 'the same'}, container_ref=image2.container_ref)
    db.session.add(mani1)
    db.session.add(mani2)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f'/v1/containers/{image1.entityName()}/{image1.collectionName()}/{image1.containerName()}/manifests')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')

    self.assertListEqual([ m['id'] for m in json ], [ str(mani1.id), str(mani2.id) ])

  
  def test_list_user(self):
    image1 = _create_image(postfix='eins')[0]
    image1.container_ref.owner = self.user

    mani1 = Manifest(content={'what': 'ever'}, container_ref=image1.container_ref)
    db.session.add(mani1)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f'/v1/containers/{image1.entityName()}/{image1.collectionName()}/{image1.containerName()}/manifests')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['id'] for c in json ], [ str(mani1.id) ])
  
  def test_list_user_denied(self):
    image1, container, collection, entity = _create_image()
    container.owner = self.other_user
    collection.owner = self.other_user
    entity.owner = self.other_user

    mani1 = Manifest(content={'what': 'ever'}, container_ref=image1.container_ref)
    db.session.add(mani1)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f'/v1/containers/{image1.entityName()}/{image1.collectionName()}/{image1.containerName()}/manifests')
    self.assertEqual(ret.status_code, 403)
  

  def test_download(self):
    image = _create_image()[0]
    image_id = image.id
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    manifest_id = manifest.id

    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 200)
    image = Image.query.get(image_id)
    self.assertEqual(ret.headers['Content-Disposition'], f'attachment; filename={image.containerName()}')
    self.assertEqual(ret.headers['Content-Type'], 'application/octet-stream')
    self.assertEqual(ret.data, b'oink')
    self.assertEqual(image.downloadCount, 1)
    self.assertEqual(image.container_ref.downloadCount, 1)

    manifest = Manifest.query.get(manifest_id)
    self.assertEqual(manifest.downloadCount, 1)

  def test_download_not_found(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()

    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id+666}/download")
    self.assertEqual(ret.status_code, 404)

  def test_download_image_not_found(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    cfg = manifest.content_json
    cfg['layers'][0]['digest'] += 'oink'
    manifest.content = cfg

    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 404)

  def test_download_image_not_uploaded(self):
    image = _create_image()[0]
    manifest = image.generate_manifest()

    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 406)

  def test_download_token(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': manifest.id,
      'type': 'manifest',
      'username': self.admin_username,
      'exp': timegm(datetime.utcnow().utctimetuple())+60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 200)

  def test_download_token_user(self):
    image = _create_image()[0]
    image.container_ref.owner = self.user
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': manifest.id,
      'type': 'manifest',
      'username': self.username,
      'exp': timegm(datetime.utcnow().utctimetuple())+60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 200)

  def test_download_token_user_denied(self):
    image = _create_image()[0]
    image.container_ref.owner = self.other_user
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': manifest.id,
      'type': 'manifest',
      'username': self.username,
      'exp': timegm(datetime.utcnow().utctimetuple())+60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 403)

  def test_download_token_expired(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': manifest.id,
      'type': 'manifest',
      'username': self.admin_username,
      'exp': timegm(datetime.utcnow().utctimetuple())-60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 401)

  def test_download_token_invalid_type(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': manifest.id,
      'type': 'grunz',
      'username': self.admin_username,
      'exp': timegm(datetime.utcnow().utctimetuple())+60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 406)

  def test_download_token_invalid_id(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()
    db.session.commit()
    token = jwt.encode({
      'id': 'grunz',
      'type': 'manifest',
      'username': self.admin_username,
      'exp': timegm(datetime.utcnow().utctimetuple())+60,
    }, self.app.config['SECRET_KEY'], algorithm='HS256')

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download?temp_token={token}")
    self.assertEqual(ret.status_code, 406)

  
  def test_download_no_auth(self):
    image = _create_image()[0]
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()

    db.session.commit()

    ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 401)

  def test_download_user(self):
    image = _create_image()[0]
    image.container_ref.owner = self.user
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()

    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 200)

  def test_download_user_denied(self):
    image = _create_image()[0]
    image.container_ref.owner = self.other_user
    tmpf = _fake_img_file(image, data=b'oink')
    manifest = image.generate_manifest()

    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/manifests/{manifest.id}/download")
    self.assertEqual(ret.status_code, 403)