import unittest
import os
import json
import datetime
from Hinkskalle.tests.route_base import RouteBase, fake_admin_auth, fake_auth

from Hinkskalle.models import Entity

class TestEntities(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    default = Entity(name='default')
    default.save()
    entity1 = Entity(name='muhkuh')
    entity1.save()
    entity2 = Entity(name='grunzschwein')
    entity2.save()

    with fake_admin_auth(self.app):
      ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 3)
    self.assertListEqual([ e['name'] for e in json ], [ default.name, entity1.name, entity2.name ] )
  
  def test_list_user(self):
    default = Entity(name='default')
    default.save()
    entity1 = Entity(name='muhkuh', createdBy='test.hase')
    entity1.save()
    entity2 = Entity(name='grunzschwein')
    entity2.save()

    with fake_auth(self.app):
      ret = self.client.get('/v1/entities')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ e['name'] for e in json ], [ default.name, entity1.name ])

  def test_get_noauth(self):
    ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 401)

  def test_get(self):
    entity = Entity(name='grunz')
    entity.save()
    with fake_admin_auth(self.app):
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
      'deletedAt': entity.deletedAt,
      'deleted': entity.deleted,
    })
  
  def test_get_default(self):
    entity = Entity(name='default')
    entity.save()

    with fake_admin_auth(self.app):
      ret = self.client.get('/v1/entities/')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user(self):
    entity = Entity(name='test.hase', createdBy='test.hase')
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get('/v1/entities/test.hase')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user_default(self):
    entity = Entity(name='default')
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get('/v1/entities/')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))

    with fake_auth(self.app):
      ret = self.client.get('/v1/entities/default')
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(entity.id))
  
  def test_get_user_other(self):
    entity = Entity(name='grunz', createdBy='someone.else')
    entity.save()

    with fake_auth(self.app):
      ret = self.client.get('/v1/entities/grunz')
    self.assertEqual(ret.status_code, 403)

  def test_create_noauth(self):
    ret = self.client.post('/v1/entities', json={
      'does': 'not matter',
    })
    self.assertEqual(ret.status_code, 401)

  def test_create(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
        'createdAt': '0001-01-01T00:00:00Z',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'grunz')
    self.assertNotEqual(data['createdAt'], '0001-01-01T00:00:00+00:00')
    self.assertEqual(data['createdBy'], 'test.hase')

  def test_create_default(self):
    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': '',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'default')

  def test_create_not_unique(self):
    entity = Entity(name='grunz')
    entity.save()

    with fake_admin_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'grunz',
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_create_user(self):
    with fake_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'test.hase',
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['name'], 'test.hase')
  
  def test_create_user_name_check(self):
    with fake_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'grunzuser'
      })
    self.assertEqual(ret.status_code, 403)

    with fake_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': 'default'
      })
    self.assertEqual(ret.status_code, 403)

    with fake_auth(self.app):
      ret = self.client.post('/v1/entities', json={
        'name': ''
      })
    self.assertEqual(ret.status_code, 403)

  def test_update(self):
    entity = Entity(name='grunz')
    entity.save()
    with fake_admin_auth(self.app):
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.objects.get(name='grunz')
    self.assertEqual(dbEntity.description, 'Oink oink')
    self.assertTrue(dbEntity.defaultPrivate)
    self.assertTrue(abs(dbEntity.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
    
    with fake_admin_auth(self.app):
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Troro',
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.objects.get(name='grunz')
    self.assertEqual(dbEntity.description, 'Troro')
    self.assertTrue(dbEntity.defaultPrivate)

  def test_update_name_change(self):
    entity = Entity(name='grunz')
    entity.save()
    with fake_admin_auth(self.app):
      ret = self.client.put('/v1/entities/grunz', json={
        'name': 'Babsi Streusand',
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.objects.get(name='grunz')
    self.assertEqual(dbEntity.name, 'grunz')

  def test_update_user(self):
    entity = Entity(name='grunz', createdBy='test.hase')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 200)

    dbEntity = Entity.objects.get(name='grunz')
    self.assertEqual(dbEntity.description, 'Oink oink')
    self.assertTrue(dbEntity.defaultPrivate)

  def test_update_user_other(self):
    entity = Entity(name='grunz', createdBy='other.hase')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.put('/v1/entities/grunz', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 403)

  def test_update_user_default(self):
    entity = Entity(name='default')
    entity.save()
    with fake_auth(self.app):
      ret = self.client.put('/v1/entities/default', json={
        'description': 'Oink oink',
        'defaultPrivate': True,
      })
    self.assertEqual(ret.status_code, 403)