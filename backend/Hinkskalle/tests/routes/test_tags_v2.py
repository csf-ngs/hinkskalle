import unittest

from Hinkskalle import db
from Hinkskalle.models import Container, Tag, Image
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.models.test_Image import _create_image

class TestTagsV2(RouteBase):
  def test_get_noauth_v2(self):
    ret = self.client.get(f"/v2/tags/whatever")
    self.assertEqual(ret.status_code, 401)

  def test_get_v2(self):
    image, container, _, _ = _create_image()
    image.arch='c64'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'c64': {}})

    container.tag_image('v1.0', image.id)
    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'c64': {'v1.0': str(image.id)} })

    container.tag_image('oink', image.id)
    with self.fake_admin_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, {'c64': {'v1.0': str(image.id), 'oink': str(image.id)}})

  def test_get_user_v2(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    image.arch='amiga'
    db.session.commit()

    container.tag_image('v1.0', str(image.id))
    with self.fake_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other_own_collection(self):
    image, container, coll, entity = _create_image()
    image.arch='amiga'
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.other_user
    db.session.commit()

    container.tag_image('v1.0', image.id)
    with self.fake_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other(self):
    image, container, coll, entity = _create_image()
    image.arch='amiga'
    entity.owner=self.other_user
    coll.owner=self.other_user
    container.owner=self.other_user
    db.session.commit()

    container.tag_image('v1.0', image.id)
    with self.fake_auth():
      ret = self.client.get(f"/v2/tags/{container.id}")
    self.assertEqual(ret.status_code, 403)
  
  def test_update_v2(self):
    image, container, _, _ = _create_image()
    container_id = container.id
    image_id = image.id
    arch_tags = {
        'apple': {
          'red': str(image.id)
        }
      }

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json=arch_tags)
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictEqual(data, arch_tags)
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {'apple': { 'red': str(image.id) }})
    db_image = Image.query.get(image_id)
    self.assertEqual(db_image.arch, 'apple')

    arch_tags = {
      'apple': {
        'blue': str(image.id)
      }
    }
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json=arch_tags)
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertDictEqual(data, {
      'apple': {
        'blue': str(image.id),
        'red': str(image.id)
      }
    })
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {'apple': { 'red': str(image.id), 'blue': str(image.id) } })
    db_image = Image.query.get(image_id)
    self.assertEqual(db_image.arch, 'apple')

  def test_valid_v2(self):
    image, container, _, _ = _create_image()
    for fail in ['Babsi Streusand', '-oink', 'Babsi&Streusand', 'oink-']:
      with self.fake_admin_auth():
        ret = self.client.post(f"/v2/tags/{container.id}", json={'c64': { fail: str(image.id)}})
      self.assertEqual(ret.status_code, 400)
  
  def test_remove_v2(self):
    image, container, _, _ = _create_image()
    image.arch='c64'
    container_id=container.id
    latest_tag = Tag(name='oink', image_ref=image)
    db.session.add(latest_tag)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'c64': { 'oink': None }})
    self.assertEqual(ret.status_code, 200)
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {'c64': {}})

  def test_remove_v2_case(self):
    image, container, _, _ = _create_image()
    image.arch='c64'
    container_id=container.id
    latest_tag = Tag(name='oInk', image_ref=image)
    db.session.add(latest_tag)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'c64': { 'OiNK': None }})
    self.assertEqual(ret.status_code, 200)
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {'c64': {}})

  def test_remove_v2_multiple(self):
    image, container, _, _ = _create_image()
    image.arch='c64'
    container_id=container.id
    latest_tag = Tag(name='oink', image_ref=image)
    image2 = Image(hash='image-2', container_ref=container, arch='amiga')
    other_tag = Tag(name='oink', image_ref=image2)
    db.session.add(latest_tag)
    db.session.add(other_tag)
    db.session.commit()
    image2_id = image2.id

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'c64': { 'oink': None }})
    self.assertEqual(ret.status_code, 200)
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {'c64': {}, 'amiga': { 'oink': str(image2_id) }})
  
  def test_update_v2_multiple(self):
    image1, container, _, _ = _create_image()
    image1.arch='c64'
    container_id=container.id
    image2 = Image(hash='image-2', container_ref=container, arch='amiga')
    db.session.add(image2)
    db.session.commit()
    image1_id=image1.id
    image2_id=image2.id

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={
        'c64': { 'v1': str(image1.id), 'latest': str(image1.id) },
        'amiga': { 'v1': str(image2.id), 'oldest': str(image2.id) },
      })
    self.assertEqual(ret.status_code, 200)
    db_container = Container.query.get(container_id)
    self.assertDictEqual(db_container.archImageTags(), {
      'c64': { 'v1': str(image1_id), 'latest': str(image1_id) },
      'amiga': { 'v1': str(image2_id), 'oldest': str(image2_id) },
    })

  def test_update_v2_invalid(self):
    image, container, _, _ = _create_image()
    image.arch='amiga'
    image_id=image.id
    container_id=container.id
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'c64': {'v1.0': 'oink'}})
    self.assertEqual(ret.status_code, 404)
    invalidid = image_id*-1

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container_id}", json={'c64': {'v1.0': invalidid}})
    self.assertEqual(ret.status_code, 404)

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/tags/{container_id}", json={'c64': {'bla&--.': image_id}})
    self.assertEqual(ret.status_code, 400)


  def test_update_v2_user(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'pear': {'v1.0': str(image.id) }})
    self.assertEqual(ret.status_code, 200)

  def test_update_v2_user_other(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/tags/{container.id}", json={'pear': {'v1.0': str(image.id) }})
    self.assertEqual(ret.status_code, 403)

  def test_update_v2_noauth(self):
    ret = self.client.post(f"/v2/tags/whatever", json={'what': 'ever'})
    self.assertEqual(ret.status_code, 401)
  