
import unittest
import os
import json
import datetime
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth, fake_auth
from Hinkskalle.models import Entity, Collection
from Hinkskalle.tests.models.test_Collection import _create_collection

class TestCollections(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/collections/whatever')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    coll1, entity = _create_collection('coll1')
    coll2, _ = _create_collection('coll2')

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 2)
    self.assertListEqual([ c['name'] for c in json ], [ coll1.name, coll2.name ] )
  
  def test_list_user(self):
    coll1, entity = _create_collection('coll1')
    coll2, _ = _create_collection('coll2')
    coll1.createdBy='test.hase'
    coll1.save()
    coll2.createdBy='test.hase'
    coll2.save()
    entity.createdBy='test.hase'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ coll1.name, coll2.name ])

  def test_list_user_default_entity(self):
    # can see own collections in default entity
    default = Entity(name='default')
    default.save()
    coll1 = Collection(name='own-1', createdBy='test.hase', entity_ref=default)
    coll1.save()
    coll2 = Collection(name='other-1', createdBy='test.kuh', entity_ref=default)
    coll2.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/default")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ coll1.name ])
  
  def test_list_user_other(self):
    coll1, entity = _create_collection('coll1')
    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 403)

  def test_get_noauth(self):
    ret = self.client.get('/v1/collections/what/ever')
    self.assertEqual(ret.status_code, 401)
  
  def test_get(self):
    coll, entity = _create_collection()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections/{coll.entityName()}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_default(self):
    coll, entity = _create_collection()
    coll.name='default'
    coll.save()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}/")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_default_entity(self):
    coll, entity = _create_collection()
    entity.name='default'
    entity.save()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections//{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))

  @unittest.skip("does not work currently, see https://github.com/pallets/flask/issues/3413")
  def test_get_default_entity_default(self):
    coll, entity = _create_collection()
    entity.name='default'
    entity.save()
    coll.name='default'
    coll.save()

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections/")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))

    with fake_admin_auth(self.app):
      ret = self.client.get(f"/v1/collections//")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_user(self):
    coll, entity = _create_collection()
    entity.createdBy='test.hase'
    entity.save()
    coll.createdBy='test.hase'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))

  def test_get_user_default_entity(self):
    coll, entity = _create_collection()
    entity.name='default'
    entity.save()
    coll.createdBy='test.hase'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_user_other_entity(self):
    coll, entity = _create_collection()
    coll.createdBy='test.hase'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)

  def test_get_user_other(self):
    coll, entity = _create_collection()
    entity.createdBy='test.hase'
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)


  def test_create_noauth(self):
    ret = self.client.post("/v1/collections")
    self.assertEqual(ret.status_code, 401)

  def test_create(self):
    entity = Entity(name='test-hase')
    entity.save()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['entity'], str(entity.id))
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_default(self):
    entity = Entity(name='test-hase')
    entity.save()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')


  def test_create_not_unique(self):
    coll, entity = _create_collection()
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': coll.name,
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_entity(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': 'oink oink',
      })
    self.assertEqual(ret.status_code, 500)

  def test_create_user(self):
    entity = Entity(name='test-hase', createdBy='test.hase')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_default_entity(self):
    entity = Entity(name='default')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 403)

  def test_create_user_default_no_name(self):
    entity = Entity(name='test-hase', createdBy='test.hase')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')

    Collection.objects.get(id=data['id']).delete()


    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'default',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
  
  def test_create_user_default_entity_reserved(self):
    entity = Entity(name='default')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'empty name')

    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'default',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'default')

    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'pipeline',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'pipeline')
  
  
  def test_create_user_other(self):
    entity = Entity(name='muh')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 403)

  def test_update(self):
    coll, entity = _create_collection()

    with fake_admin_auth(self.app):
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 200)

    dbColl = Collection.objects.get(name=coll.name)
    self.assertEqual(dbColl.description, 'Mei Huat')
    self.assertTrue(dbColl.private)
    self.assertEqual(dbColl.customData, 'hot drei Eckn')

    self.assertTrue(abs(dbColl.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))

  def test_update_user(self):
    coll, entity = _create_collection()
    entity.createdBy='test.hase'
    entity.save()
    coll.createdBy='test.hase'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 200)

    dbColl = Collection.objects.get(name=coll.name)
    self.assertEqual(dbColl.description, 'Mei Huat')
    self.assertTrue(dbColl.private)
    self.assertEqual(dbColl.customData, 'hot drei Eckn')

  def test_update_user_other(self):
    coll, entity = _create_collection()
    entity.createdBy='test.hase'
    entity.save()
    coll.createdBy='test.ziege'
    coll.save()

    with fake_auth(self.app):
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 403)