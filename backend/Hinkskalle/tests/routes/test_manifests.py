from Hinkskalle import db
from ..route_base import RouteBase

from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.models.Manifest import Manifest

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
