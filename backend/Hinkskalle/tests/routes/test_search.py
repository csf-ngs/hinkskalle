import unittest

from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.tests.models.test_Image import _create_image
from Hinkskalle.tests.models.test_Container import _create_container

from Hinkskalle import db
from Hinkskalle.models import ContainerSchema, EntitySchema, CollectionSchema

class TestSearch(RouteBase):
  def test_search_noauth(self):
    ret = self.client.get('/v1/search?value=something')
    self.assertEqual(ret.status_code, 401)
  
  def test_search_container(self):
    container, _, _ = _create_container()
    container.name='ptERANodon'
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [],
      'image': [],
      'container': [ ContainerSchema().dump(container).data ]
    }

    for search in [container.name, container.name[3:6], container.name[3:6].lower()]:
      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/search?value={search}")
      self.assertEqual(ret.status_code, 200)
      json = ret.get_json().get('data')
      self.assertDictEqual(json, expected)


  def test_search_entity(self):
    _, _, entity = _create_container()
    entity.name='ptERANodon'
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [ EntitySchema().dump(entity).data ],
      'image': [],
      'container': []
    }

    for search in [entity.name, entity.name[3:6], entity.name[3:6].lower()]:
      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/search?value={search}")
      self.assertEqual(ret.status_code, 200)
      json = ret.get_json().get('data')
      self.assertDictEqual(json, expected)

  def test_search_collection(self):
    _, collection, _ = _create_container()
    collection.name='ptERANodon'
    db.session.commit()

    expected = {
      'collection': [ CollectionSchema().dump(collection).data ],
      'entity': [],
      'image': [],
      'container': []
    }

    for search in [collection.name, collection.name[3:6], collection.name[3:6].lower()]:
      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/search?value={search}")
      self.assertEqual(ret.status_code, 200)
      json = ret.get_json().get('data')
      self.assertDictEqual(json, expected)
  
  def test_all(self):
    container, collection, entity = _create_container()
    entity.name='oink-entity'
    collection.name="oink-collection"
    container.name="oink-container"
    db.session.commit()

    expected = {
      'collection': [ CollectionSchema().dump(collection).data ],
      'entity': [ EntitySchema().dump(entity).data ],
      'container': [ ContainerSchema().dump(container).data ],
      'image': []
    }

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/search?value=oink")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertDictEqual(json, expected)

  def test_user(self):
    container, collection, entity = _create_container()

    expected = {
      'collection': [],
      'entity': [],
      'container': [],
      'image': [],
    }

    for search in [ container.name, collection.name, entity.name ]:
      with self.fake_auth():
        ret = self.client.get(f"/v1/search?value={search}")
      self.assertEqual(ret.status_code, 200)
      self.assertDictEqual(ret.get_json().get('data'), expected)
  
  def test_user_access(self):
    container, _, entity = _create_container()
    container.name='testhase'
    entity.name='default'
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [],
      'container': [ ContainerSchema().dump(container).data ],
      'image': []
    }

    with self.fake_auth():
      ret = self.client.get(f"/v1/search?value={container.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual(ret.get_json().get('data'), expected)

  def test_user_access_owned(self):
    container, _, entity = _create_container()
    container.name='testhase'
    entity.owner=self.user
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [],
      'container': [ ContainerSchema().dump(container).data ],
      'image': []
    }

    with self.fake_auth():
      ret = self.client.get(f"/v1/search?value={container.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual(ret.get_json().get('data'), expected)
  
  def test_description(self):
    container, _, _ = _create_container()
    container.description='aNkyLOSaurUS'
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [],
      'container': [ ContainerSchema().dump(container).data ],
      'image': []
    }

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/search?description={container.description}")
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual(ret.get_json().get('data'), expected)

  def test_description_value(self):
    container, _, _ = _create_container()
    container2, _, _ = _create_container('oink')
    container.description='aNkyLOSaurUS'
    container2.description=container.description
    db.session.commit()

    expected = {
      'collection': [],
      'entity': [],
      'container': [ ContainerSchema().dump(container).data ],
      'image': []
    }

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/search?description={container.description}&value={container.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual(ret.get_json().get('data'), expected)
