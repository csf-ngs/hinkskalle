
import unittest
import os
import json
import datetime
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.models import Entity, Collection, Container
from Hinkskalle.tests.models.test_Collection import _create_collection
from Hinkskalle import db

class TestCollections(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/collections/whatever')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    coll1, entity = _create_collection('coll1')
    coll2, _ = _create_collection('coll2')

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 2)
    self.assertListEqual([ c['name'] for c in json ], [ coll1.name, coll2.name ] )
  
  def test_list_user(self):
    coll1, entity = _create_collection('coll1')
    coll2, _ = _create_collection('coll2')

    coll1_id=coll1.id
    coll2_id=coll2.id

    coll1.owner=self.user
    coll2.owner=self.user
    entity.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    # coll1 and coll2 lost from session??
    read_coll1 = Collection.query.get(coll1_id)
    read_coll2 = Collection.query.get(coll2_id)
    self.assertListEqual([ c['name'] for c in json ], [ read_coll1.name, read_coll2.name ])

  def test_list_user_default_entity(self):
    # can see own collections in default entity
    default = Entity(name='default')
    db.session.add(default)
    coll1 = Collection(name='own-1', owner=self.user, entity_ref=default)
    db.session.add(coll1)
    coll2 = Collection(name='other-1', owner=self.other_user, entity_ref=default)
    db.session.add(coll2)
    db.session.commit()
    coll1_id = coll1.id
    coll2_id = coll2.id

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/default")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    read_coll1 = Collection.query.get(coll1_id)
    read_coll2 = Collection.query.get(coll2_id)
    self.assertListEqual([ c['name'] for c in json ], [ read_coll1.name, read_coll2.name ])
  
  def test_list_user_other(self):
    coll1, entity = _create_collection('coll1')
    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}")
    self.assertEqual(ret.status_code, 403)

  def test_get_noauth(self):
    ret = self.client.get('/v1/collections/what/ever')
    self.assertEqual(ret.status_code, 401)
  
  def test_get(self):
    coll, entity = _create_collection()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections/{coll.entityName()}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))

  def test_get_case(self):
    coll, _ = _create_collection('TestHase')
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections/Test-Hase/TestHase")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data').get('id'), str(coll.id))

  
  def test_get_default(self):
    coll, entity = _create_collection()
    coll.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')

    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_default_entity(self):
    coll, entity = _create_collection()
    entity.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections//{coll.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/collections/default/{coll.name}$")
    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))

  #@unittest.skip("does not work currently, see https://github.com/pallets/flask/issues/3413")
  def test_get_default_entity_default(self):
    coll, entity = _create_collection()
    entity.name='default'
    db.session.commit()
    coll.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections/")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/collections//")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/collections/default/$")
    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_user(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    db.session.commit()
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))

  def test_get_user_default_entity(self):
    coll, entity = _create_collection()
    entity.name='default'
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(coll.id))
  
  def test_get_user_other_entity(self):
    coll, entity = _create_collection()
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other_own_entity(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other(self):
    coll, entity = _create_collection()
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)


  def test_create_noauth(self):
    ret = self.client.post("/v1/collections")
    self.assertEqual(ret.status_code, 401)

  def test_create(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['entity'], str(entity.id))
    self.assertEqual(data['createdBy'], self.admin_username)

    db_collection = Collection.query.get(data['id'])
    self.assertTrue(abs(db_collection.createdAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))

  def test_create_behalf(self):
    entity = Entity(name='test-hase', owner=self.user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    db_collection = Collection.query.filter(Collection.name=='oink', Collection.entity_id==entity.id).first()
    self.assertEqual(db_collection.owner.username, self.username)

  def test_create_check_name(self):
    entity  = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()

    for fail in ['Babsi Streusand', '-oink', 'Babsi&Streusand', 'oink-']:
      with self.fake_admin_auth():
          ret = self.client.post('/v1/collections', json={
            'name': fail,
            'entity': str(entity.id),
          })
      self.assertEqual(ret.status_code, 400)
  
  def test_create_defaultPrivate(self):
    entity = Entity(name='test-hase')
    entity.defaultPrivate = True
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    dbColl = Collection.query.get(data['id'])
    self.assertTrue(dbColl.private)

    # why do I need to refetch from db?? entity seems to be
    # gone from session.
    entity = Entity.query.get(entity.id)
    entity.defaultPrivate = False
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'auch.oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    dbColl = Collection.query.get(data['id'])
    self.assertFalse(dbColl.private)



  def test_create_default(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')


  def test_create_not_unique(self):
    coll, entity = _create_collection()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': coll.name,
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 412)

  def test_create_not_unique_case(self):
    coll, entity = _create_collection()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': coll.name.upper(),
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_entity(self):
    with self.fake_admin_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': -666,
      })
    self.assertEqual(ret.status_code, 400)

  def test_create_user(self):
    entity = Entity(name='test-hase', owner=self.user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_default_entity(self):
    entity = Entity(name='default')
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 403)

  def test_create_user_default_no_name(self):
    entity = Entity(name='test-hase', owner=self.user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')

    Collection.query.filter(Collection.id==data['id']).delete()


    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'default',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 200)
  
  def test_create_user_default_entity_reserved(self):
    entity = Entity(name='default')
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': '',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'empty name')

    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'default',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'default')

    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'pipeline',
        'entity': str(entity.id)
      })
    self.assertEqual(ret.status_code, 403, 'pipeline')
  
  
  def test_create_user_other(self):
    entity = Entity(name='muh')
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.post('/v1/collections', json={
        'name': 'oink',
        'entity': str(entity.id),
      })
    self.assertEqual(ret.status_code, 403)

  def test_update(self):
    coll, entity = _create_collection()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 200)

    dbColl = Collection.query.filter(Collection.name==coll.name).one()
    self.assertEqual(dbColl.description, 'Mei Huat')
    self.assertTrue(dbColl.private)
    self.assertEqual(dbColl.customData, 'hot drei Eckn')

    self.assertTrue(abs(dbColl.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
  
  def test_update_case(self):
    coll, _ = _create_collection('testhase')

    with self.fake_admin_auth():
      ret = self.client.put("/v1/collections/Test-Hase/TestHase", json={
        'description': 'Mei Huat',
      })
    self.assertEqual(ret.status_code, 200)
    dbColl = Collection.query.filter(Collection.name==coll.name).one()
    self.assertEqual(dbColl.description, 'Mei Huat')


  
  def test_update_owner(self):
    coll, entity = _create_collection()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'createdBy': self.other_username
      })
    
    self.assertEqual(ret.status_code, 200)
    dbColl = Collection.query.filter(Collection.name==coll.name).one()
    self.assertEqual(dbColl.createdBy, self.other_username)


  def test_update_user(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    db.session.commit()
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 200)

    dbColl = Collection.query.filter(Collection.name==coll.name).one()
    self.assertEqual(dbColl.description, 'Mei Huat')
    self.assertTrue(dbColl.private)
    self.assertEqual(dbColl.customData, 'hot drei Eckn')
  
  def test_update_user_owner(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'createdBy': self.other_username
      })
    self.assertEqual(ret.status_code, 403)
    dbColl = Collection.query.filter(Collection.name==coll.name).one()
    self.assertEqual(dbColl.createdBy, self.username)

    with self.fake_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'createdBy': self.username
      })
    self.assertEqual(ret.status_code, 200)

  def test_update_user_other(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    db.session.commit()
    coll.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/collections/{entity.name}/{coll.name}", json={
        'description': 'Mei Huat',
        'private': True,
        'customData': 'hot drei Eckn',
      })
    self.assertEqual(ret.status_code, 403)

  def test_delete(self):
    coll, entity = _create_collection()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Collection.query.filter(Collection.name==coll.name).first())
  
  def test_delete_case(self):
    coll, _ = _create_collection("TestHase")
    with self.fake_admin_auth():
      ret = self.client.delete("/v1/collections/Test-Hase/TestHase")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Collection.query.filter(Collection.name==coll.name).first())
  
  def test_delete_not_empty(self):
    coll, entity = _create_collection()
    container = Container(name="test-conti1", collection_id=coll.id)
    db.session.add(container)
    db.session.commit()


    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 412)

  def test_delete_user(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Collection.query.filter(Collection.name==coll.name).first())

  def test_delete_user_other(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    db.session.commit()
    coll.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/collections/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)

  def test_delete_noauth(self):
    ret = self.client.delete("/v1/collections/oi/nk")
    self.assertEqual(ret.status_code, 401)