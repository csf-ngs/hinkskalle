from sqlalchemy.orm.exc import NoResultFound # type: ignore
from ..route_base import RouteBase
from .._util import _create_user, _create_container

from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.User import User
from Hinkskalle import db

import datetime

class TestUsers(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/users')
    self.assertEqual(ret.status_code, 401)
  
  def test_get_noauth(self):
    ret = self.client.get('/v1/users/test.hase')
    self.assertEqual(ret.status_code, 401)
  
  def test_post_noauth(self):
    ret = self.client.post('/v1/users', json={ 'username': 'test.hase' })
    self.assertEqual(ret.status_code, 401)
  
  def test_put_noauth(self):
    ret = self.client.put('/v1/users/test.hase', json={ 'username': 'test.hase' })
    self.assertEqual(ret.status_code, 401)
  
  def test_delete_noauth(self):
    ret = self.client.delete('/v1/users/test.hase')
    self.assertEqual(ret.status_code, 401)
  
  def test_list(self):
    user1 = _create_user('test.hase')
    user2 = _create_user('test.kuh')

    with self.fake_admin_auth():
      ret = self.client.get('/v1/users')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 5)
    self.assertListEqual([ u['username'] for u in json ], [ self.admin_username, self.username, self.other_username, user1.username, user2.username ])
  
  def test_list_user(self):
    user1 = _create_user('test.hase')
    user2 = _create_user('test.kuh')

    with self.fake_auth():
      ret = self.client.get('/v1/users')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 5)
    self.assertListEqual([ u['username'] for u in json ], [ self.admin_username, self.username, self.other_username, user1.username, user2.username ])
  
  def test_list_user_query(self):
    user1 = _create_user('test.schaf')
    user2 = _create_user('test.kuh')

    with self.fake_auth():
      ret = self.client.get('/v1/users?username=schaf')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ u['username'] for u in json ], [ 'test.schaf' ])

    with self.fake_auth():
      ret = self.client.get('/v1/users?username=test')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ u['username'] for u in json ], [ 'test.schaf', 'test.kuh' ])
  

  def test_get(self):
    user1 = _create_user('test.hase')
    
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{user1.username}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    json.pop('createdAt')
    self.assertDictEqual(json, {
      "id": str(user1.id),
      "username": user1.username,
      "email": user1.email,
      "firstname": user1.firstname,
      "lastname": user1.lastname,
      "isAdmin": user1.is_admin,
      "isActive": user1.is_active,
      "source": user1.source,
      "createdBy": user1.createdBy,
      "updatedAt": user1.updatedAt,
      "deletedAt": None,
      "deleted": False,
      "groups": [],
    })
  
  def test_get_user_self(self):
    db_user = User.query.filter(User.username==self.username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(db_user.id))

  
  def test_get_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(db_user.id))
  

  def test_get_stars(self):
    user1 = _create_user('test.hasee')
    container = _create_container()[0]
    user1.starred.append(container)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{user1.username}/stars")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])
  
  def test_get_stars_user_self(self):
    db_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    container.owner = db_user
    db_user.starred.append(container)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}/stars")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])

  def test_get_stars_user_self_other(self):
    db_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    db_user.starred.append(container)

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}/stars")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [])
  
  def test_get_stars_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}/stars")
    self.assertEqual(ret.status_code, 403)

  def test_star_container(self):
    user1 = _create_user('test.hasee')
    container = _create_container()[0]

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/users/{user1.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])
    db_user = User.query.filter(User.username==user1.username).one()
    self.assertListEqual([ c.id for c in db_user.starred ], [ container.id ])

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/users/{user1.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])
  
  def test_unstar_container(self):
    user1 = _create_user()
    container = _create_container()[0]
    user1.starred.append(container)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/users/{user1.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertEqual(len(json), 0)

  def test_unstar_container_not_starred(self):
    user1 = _create_user()
    container = _create_container()[0]

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/users/{user1.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 404)
  
  def test_star_container_user_self(self):
    db_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    container.owner = db_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{db_user.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])

  def test_unstar_container_user_self(self):
    db_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    container.owner = db_user
    db_user.starred.append(container)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{db_user.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertEqual(len(json), 0)

  def test_unstar_container_user_self_other(self):
    db_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    db_user.starred.append(container)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{db_user.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertEqual(len(json), 0)

  def test_star_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()
    self_user = User.query.filter(User.username==self.username).one()
    container = _create_container()[0]
    container.owner = self_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{db_user.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 403)

  def test_unstar_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()
    container = _create_container()[0]
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{db_user.username}/stars/{container.id}")
    self.assertEqual(ret.status_code, 403)
  
  def test_register_disabled(self):
    self.app.config['ENABLE_REGISTER']=False
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'password': 'geheimbaer',
    }
    ret = self.client.post('/v1/register', json=user_data)
    self.assertEqual(ret.status_code, 403)
  
  def test_register(self):
    self.app.config['ENABLE_REGISTER']=True
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'password': 'geheimbaer',
    }

    ret = self.client.post('/v1/register', json=user_data)
    self.assertEqual(ret.status_code, 200)

    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['username'], user_data['username'])
    db_user = User.query.get(data['id'])
    for f in ['email', 'firstname', 'lastname']:
      self.assertEqual(getattr(db_user, f), user_data[f])
    self.assertTrue(db_user.check_password(user_data['password']))
    self.assertTrue(db_user.is_active)
    self.assertFalse(db_user.is_admin)
    self.assertIsNone(db_user.createdBy)
    self.assertTrue(abs(db_user.createdAt - datetime.datetime.now()) < datetime.timedelta(seconds=2))

    db_entity = Entity.query.filter(Entity.name==user_data['username']).first()
    self.assertIsNotNone(db_entity)
    self.assertEqual(db_entity.createdBy, db_user.username)

  def test_register_exists(self):
    self.app.config['ENABLE_REGISTER']=True
    user = _create_user('probier.hase')
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'password': 'geheimbaer',
    }

    ret = self.client.post('/v1/register', json=user_data)
    self.assertEqual(ret.status_code, 412)

  def test_register_entity_exists(self):
    self.app.config['ENABLE_REGISTER']=True
    entity = Entity(name='probier.hase')
    db.session.add(entity)
    db.session.commit()
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'password': 'geheimbaer',
    }

    ret = self.client.post('/v1/register', json=user_data)
    self.assertEqual(ret.status_code, 412)

    
  def test_create(self):
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'source': 'Mars',
      'isAdmin': True,
      'isActive': False,
      'password': 'geheimhase',
    }
    with self.fake_admin_auth():
      ret = self.client.post('/v1/users', json=user_data)
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['username'], user_data['username'])
    db_user = User.query.get(data['id'])
    for f in ['email', 'firstname', 'lastname', 'source', 'isAdmin', 'isActive']:
      uf = 'is_active' if f == 'isActive' else 'is_admin' if f == 'isAdmin' else f
      self.assertEqual(getattr(db_user, uf), user_data[f])
    self.assertTrue(db_user.check_password(user_data['password']))
    self.assertEqual(db_user.createdBy, self.admin_username)
    self.assertTrue(abs(db_user.createdAt - datetime.datetime.now()) < datetime.timedelta(seconds=2))
  
  def test_create_entity(self):
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'source': 'Mars',
      'isAdmin': True,
      'isActive': False,
      'password': 'geheimhase',
    }
    with self.fake_admin_auth():
      ret = self.client.post('/v1/users', json=user_data)
    self.assertEqual(ret.status_code, 200)
    
    try:
      dbEntity = Entity.query.filter(Entity.name==user_data['username']).one()
    except NoResultFound:
      self.fail('db entity not found')
    self.assertEqual(dbEntity.createdBy, user_data['username'])

  def test_create_entity_exists(self):
    user_data = {
      'username': 'probier.hase',
      'email': 'probier@ha.se',
      'firstname': 'Probier',
      'lastname': 'Hase',
      'source': 'Mars',
      'isAdmin': True,
      'isActive': False,
      'password': 'geheimhase',
    }
    entity = Entity(name=user_data['username'])
    db.session.add(entity)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/users', json=user_data)
    self.assertEqual(ret.status_code, 412)
    json = ret.get_json()
    self.assertRegexpMatches(json.get('message'), r'entity.*already exists') # type: ignore
    
  
  def test_create_not_unique(self):
    existing = _create_user()
    username = existing.username

    for f in ['username', 'email']:
      existing = User.query.filter(User.username==username).one()
      new_user = {
        'username': 'probier.hase',
        'email': 'probier@ha.se',
        'firstname': 'Probier',
        'lastname': 'Hase',
      }
      new_user[f]=getattr(existing, f)
      with self.fake_admin_auth():
        ret = self.client.post("/v1/users", json=new_user)
      self.assertEqual(ret.status_code, 412)
      json = ret.get_json()
      self.assertRegexpMatches(json.get('message'), r'User.*already exists') # type: ignore


  def test_create_user(self):
    with self.fake_auth():
      ret = self.client.post('/v1/users', json={'oi': 'nk'})
    self.assertEqual(ret.status_code, 403)
    
  def test_update(self):
    user = _create_user('update.hase')

    update_data = {
      "email": "oi@nk",
      "firstname": "Eins",
      "lastname": "Oida",
      "source": "Mars",
      "isAdmin": True,
      "isActive": False,
    }
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json=update_data)

    self.assertEqual(ret.status_code, 200)

    db_user = User.query.get(user.id)
    for f in ['email', 'firstname', 'lastname', 'source', 'isAdmin', 'isActive']:
      uf = 'is_active' if f == 'isActive' else 'is_admin' if f == 'isAdmin' else f
      self.assertEqual(getattr(db_user, uf), update_data[f])
    self.assertTrue(abs(db_user.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=2))

  def test_update_password(self):
    user_data = {
      "password": "supergeheim, supergeheim",
    }
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json=user_data)
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.filter(User.username==self.username).one()
    self.assertTrue(db_user.check_password(user_data['password']))
  
  def test_update_nonlocal(self):
    user = _create_user('update.hase')
    user.is_active = False
    user.is_admin = False
    user.source = 'thin air'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={
        'email': 'wos.aun@das',
        'firstname': 'aundasupdate',
        'lastname': 'aundashase',
        'isActive': True,
        'isAdmin': True,
      })
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.filter(User.username=='update.hase').one()
    self.assertNotEqual(db_user.email, 'wus.aun@das')
    self.assertNotEqual(db_user.firstname, 'aundasupdate')
    self.assertNotEqual(db_user.lastname, 'aundashase')
    self.assertTrue(db_user.is_active)
    self.assertTrue(db_user.is_admin)

  
  def test_update_username_change(self):
    user = _create_user('update.hase')

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": "hase.update" })
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.get(user.id)
    self.assertEqual(db_user.username, 'hase.update')

  def test_update_username_change_entity(self):
    user = _create_user('update.hase')
    entity = Entity(name=user.username, owner=user)
    db.session.add(entity)
    db.session.commit()
    entity_id=entity.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": "hase.update" })
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.get(user.id)
    self.assertEqual(db_user.username, 'hase.update')

    db_entity = Entity.query.get(entity_id)
    self.assertEqual(db_entity.name, db_user.username)

  def test_update_username_change_entity_not_owned(self):
    user = _create_user('update.hase')
    entity = Entity(name=user.username, owner=self.other_user)
    db.session.add(entity)
    db.session.commit()
    entity_id=entity.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": "hase.update" })
    
    self.assertEqual(ret.status_code, 412)
    self.assertRegexpMatches(ret.get_json().get('message'), 'Cannot rename entity') # type: ignore
  
  def test_update_username_collision(self):
    user = _create_user('update.user')
    other_user = _create_user('hase.update')

    user_id = user.id
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": other_user.username })
    self.assertEqual(ret.status_code, 409)
    db_user = User.query.get(user_id)
    self.assertEqual(db_user.username, 'update.user')
  
  def test_update_username_entity_collision(self):
    user = _create_user('update.hase')
    entity = Entity(name=user.username, owner=user)
    other_entity = Entity(name='hase.update')

    db.session.add(entity)
    db.session.add(other_entity)
    db.session.commit()

    user_id = user.id
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": other_entity.name })
    self.assertEqual(ret.status_code, 409)

    db_user = User.query.get(user_id)
    self.assertEqual(db_user.username, 'update.hase')
  
  def test_update_user(self):
    user_data = {
      "username": "wer.anders",
      "email": "wo@ande.rs",
      "firstname": "Zwerg",
      "lastname": "Nase",
    }
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json=user_data)
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.filter(User.username==user_data['username']).one()
    self.assertEqual(db_user.username, user_data['username'])
    self.assertEqual(db_user.email, user_data['email'])
    self.assertEqual(db_user.firstname, user_data['firstname'])
    self.assertEqual(db_user.lastname, user_data['lastname'])
  
  def test_update_password_user(self):
    user_data = {
      "password": "supergeheim, supergeheim",
      'oldPassword': 'supergeheim',
    }
    self.user.set_password('supergeheim')
    db.session.commit()
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json=user_data)
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.filter(User.username==self.username).one()
    self.assertTrue(db_user.check_password(user_data['password']))

  def test_update_password_user_missing_old(self):
    user_data = {
      "password": "supergeheim, supergeheim",
    }
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json=user_data)
    
    self.assertEqual(ret.status_code, 412)

  def test_update_password_user_wrong_old(self):
    user_data = {
      "password": "supergeheim, supergeheim",
      'oldPassword': 'oink'
    }
    self.user.set_password('supergeheim')
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json=user_data)
    
    self.assertEqual(ret.status_code, 403)
  
  def test_update_user_forbidden(self):
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json={ 'source': 'nile' })
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json={ 'isAdmin': True })
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}", json={ 'isActive': False })
    self.assertEqual(ret.status_code, 403)
  
  def test_update_user_other(self):
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.other_username}", json={ 'firstname': 'irgendwas' })
    self.assertEqual(ret.status_code, 403)

  def test_delete(self):
    user = _create_user('verschwind.hase')

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/users/{user.username}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(User.query.filter(User.username==user.username).first())
  
  def test_delete_user(self):
    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.username}")
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.other_username}")
    self.assertEqual(ret.status_code, 403)






    





  
