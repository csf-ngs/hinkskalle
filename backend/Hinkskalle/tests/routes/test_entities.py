import unittest
import os
import json
import datetime
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.models import Entity, Collection
from Hinkskalle import db

class TestEntities(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    default = Entity(name='default')
    db.session.add(default)
    entity1 = Entity(name='muhkuh')
    db.session.add(entity1)
    entity2 = Entity(name='grunzschwein')
    db.session.add(entity2)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 3)
    self.assertListEqual([ e['name'] for e in json ], [ default.name, entity1.name, entity2.name ] )
  
  def test_list_user(self):
    default = Entity(name='default')
    db.session.add(default)
    entity1 = Entity(name='muhkuh', owner=self.user)
    db.session.add(entity1)
    entity2 = Entity(name='grunzschwein')
    db.session.add(entity2)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ e['name'] for e in json ], [ default.name, entity1.name ])

  def test_get_noauth(self):
    ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 401)

  def test_get(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json()
    json['data'].pop('createdAt')
    self.assertDictEqual(json['data'], {
      'id': str(entity.id),
      'name': entity.name,
      'description': entity.description,
      'customData': entity.customData,
      'quota': entity.quota,
      'size': entity.size(),
      'defaultPrivate': entity.defaultPrivate,
      #'createdAt': entity.createdAt.isoformat('T', timespec='milliseconds'),
      'createdBy': entity.createdBy,
      'updatedAt': entity.updatedAt,
      'deletedAt': None,
      'deleted': False,
    })
  
  def test_get_case(self):
    entity = Entity(name='testhase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.get('/v1/entities/TestHase')
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data')['id'], str(entity.id))
  
  def test_get_default(self):
    entity = Entity(name='default')
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get('/v1/entities/')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user(self):
    entity = Entity(name='test.hase', owner=self.user)
    db.session.add(entity)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/entities/test.hase')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user_default(self):
    entity = Entity(name='default')
    db.session.add(entity)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/entities/')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))

    with self.fake_auth():
      ret = self.client.get('/v1/entities/default')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user_other(self):
    entity = Entity(name='grunz', owner=self.other_user)
    db.session.add(entity)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 403)

  def test_create_noauth(self):
    ret = self.client.post('/v1/entities', json={
      'does': 'not matter',
    })
    self.assertEqual(ret.status_code, 401)

  def test_create(self):
    with self.fake_admin_auth():
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'grunz')
    self.assertEqual(data['createdBy'], self.admin_username)

    db_entity = Entity.query.get(data['id'])
    self.assertTrue(abs(db_entity.createdAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
  
  def test_create_check_name(self):
    for fail in ['Babsi Streusand', '-oink', '_oink', '.oink', 'Babsi&Streusand', 'oink-', 'oink.', 'oink_']:
      with self.fake_admin_auth():
          ret = self.client.post('/v1/entities', json={
            'name': fail
          })
      self.assertEqual(ret.status_code, 400, f"check {fail}")
    for good in ['test_hase', 'test.hase', 'test-hase', 'Test-Kuh']:
      with self.fake_admin_auth():
        ret = self.client.post('/v1/entities', json={
          'name': good
        })
      self.assertEqual(ret.status_code, 200, f"check good {good}")


  def test_create_default(self):
    with self.fake_admin_auth():
      ret = self.client.post('/v1/entities', json={
        'name': '',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')

  def test_create_not_unique(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
      })
    self.assertEqual(ret.status_code, 412)

  def test_create_not_unique_case(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/entities', json={
        'name': 'GRUNZ',
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_create_user(self):
    with self.fake_auth():
      ret = self.client.post('/v1/entities', json={
        'name': self.username,
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], self.username)
  
  def test_create_user_name_check(self):
    with self.fake_auth():
      ret = self.client.post('/v1/entities', json={
        'name': 'grunzuser'
      })
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.post('/v1/entities', json={
        'name': 'default'
      })
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.post('/v1/entities', json={
        'name': ''
      })
    self.assertEqual(ret.status_code, 403)

  def test_update(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.description, 'Oink oink')
    self.assertTrue(dbEntity.defaultPrivate)
    self.assertTrue(abs(dbEntity.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
    
    with self.fake_admin_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Troro',
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.description, 'Troro')
    self.assertTrue(dbEntity.defaultPrivate)
  
  def test_update_case(self):
    entity = Entity(name='testhase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.put('/v1/entities/TestHase', json={
        'description': 'Oink oink'
      })
    self.assertEqual(ret.status_code, 200)
    dbEntity = Entity.query.filter(Entity.name=='testhase').one()
    self.assertEqual(dbEntity.description, 'Oink oink')
  
  def test_update_owner(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'createdBy': self.other_username,
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.createdBy, self.other_username)


  def test_update_name_change(self):
    entity = Entity(name='grunz')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'name': 'babsi-streusand',
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.name, 'grunz')

  def test_update_user(self):
    entity = Entity(name='grunz', owner=self.user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.description, 'Oink oink')
    self.assertTrue(dbEntity.defaultPrivate)

  def test_update_user_owner(self):
    entity = Entity(name='grunz', owner=self.user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'createdBy': self.other_username,
      })
    self.assertEqual(ret.status_code, 403)

    dbEntity = Entity.query.filter(Entity.name=='grunz').one()
    self.assertEqual(dbEntity.createdBy, self.username)

    with self.fake_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'createdBy': self.username,
      })
    self.assertEqual(ret.status_code, 200)

  def test_update_user_other(self):
    entity = Entity(name='grunz', owner=self.other_user)
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 403)

  def test_update_user_default(self):
    entity = Entity(name='default')
    db.session.add(entity)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.put('/v1/entities/default', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 403)
  
  def test_delete(self):
    entity = Entity(name='testhase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/entities/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertIsNone(Entity.query.filter(Entity.name==entity.name).first())
  
  def test_delete_case(self):
    entity = Entity(name='testhase')
    db.session.add(entity)
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.delete("/v1/entities/TestHase")
    self.assertEqual(ret.status_code, 200)
    self.assertIsNone(Entity.query.filter(Entity.name==entity.name).first())

  
  def test_delete_not_empty(self):
    entity = Entity(name='testhase')
    db.session.add(entity)
    collection = Collection(name='test-coll1', entity_ref=entity)
    db.session.add(collection)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/entities/{entity.name}")
    self.assertEqual(ret.status_code, 412)
  
  def test_delete_user(self):
    entity = Entity(name='testhase', owner=self.user)
    db.session.add(entity)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/entities/{entity.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertIsNone(Entity.query.filter(Entity.name==entity.name).first())

  def test_delete_user_other(self):
    entity = Entity(name='testhase', owner=self.other_user)
    db.session.add(entity)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/entities/{entity.name}")
    self.assertEqual(ret.status_code, 403)
  
  def test_delete_noauth(self):
    ret = self.client.delete("/v1/entities/oink")
    self.assertEqual(ret.status_code, 401)
