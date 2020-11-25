import unittest
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.model_base import _create_user
from Hinkskalle.tests.models.test_Container import _create_container

from Hinkskalle.models import User
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
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 5)
    self.assertListEqual([ u['username'] for u in json ], [ self.admin_username, self.username, self.other_username, user1.username, user2.username ])
  
  def test_list_user(self):
    user1 = _create_user('test.hase')
    user2 = _create_user('test.kuh')

    with self.fake_admin_auth():
      ret = self.client.get('/v1/users')
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 5)
    self.assertListEqual([ u['username'] for u in json ], [ self.admin_username, self.username, self.other_username, user1.username, user2.username ])


  def test_get(self):
    user1 = _create_user('test.hase')
    
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{user1.username}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
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
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(db_user.id))

  
  def test_get_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['id'], str(db_user.id))
  
  def test_get_stars(self):
    user1 = _create_user('test.hasee')
    container = _create_container()[0]
    user1.starred.append(container)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{user1.username}/stars")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertListEqual([ c['name'] for c in json ], [ container.name ])
  
  def test_get_stars_user_self(self):
    db_user = User.query.filter(User.username==self.username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}/stars")
    self.assertEqual(ret.status_code, 200)
  
  def test_get_stars_user_other(self):
    db_user = User.query.filter(User.username==self.other_username).one()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{db_user.username}/stars")
    self.assertEqual(ret.status_code, 403)


    
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
    data = ret.get_json().get('data')
    self.assertEqual(data['username'], user_data['username'])
    db_user = User.query.get(data['id'])
    for f in ['email', 'firstname', 'lastname', 'source', 'isAdmin', 'isActive']:
      uf = 'is_active' if f == 'isActive' else 'is_admin' if f == 'isAdmin' else f
      self.assertEqual(getattr(db_user, uf), user_data[f])
    self.assertTrue(db_user.check_password(user_data['password']))
    self.assertEqual(db_user.createdBy, self.admin_username)
    self.assertTrue(abs(db_user.createdAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
  
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
    self.assertTrue(abs(db_user.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=1))
  
  def test_update_username_change(self):
    user = _create_user('update.hase')

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{user.username}", json={ "username": "hase.update" })
    
    self.assertEqual(ret.status_code, 200)
    db_user = User.query.get(user.id)
    self.assertEqual(db_user.username, 'hase.update')
  
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






    





  
