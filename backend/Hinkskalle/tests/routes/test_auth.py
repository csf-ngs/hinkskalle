import unittest
from flask import g
from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.tests.model_base import _create_user
from Hinkskalle.models import User, Token
from Hinkskalle import db

class TestPasswordAuth(RouteBase):
  def test_password(self):
    user = _create_user(name='oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': user.username, 'password': 'supergeheim' } )
      self.assertEqual(ret.status_code, 200)
      self.assertIn('authenticated_user', g)
      self.assertEqual(g.authenticated_user, user)

    data = ret.get_json().get('data')
    self.assertIn('id', data)

    self.assertEqual(len(user.tokens), 1)
    db_token = Token.query.filter(Token.id==data['id'])
    self.assertIsNotNone(db_token)
  
  def test_password_fail(self):
    user = _create_user(name='oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': user.username, 'password': 'superfalsch' } )
      self.assertEqual(ret.status_code, 401)
      self.assertIsNone(g.get('authenticated_user'))
    
  def test_password_user_not_found(self):
    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': 'gits.net', 'password': 'superfalsch' } )
      self.assertEqual(ret.status_code, 401)
      self.assertIsNone(g.get('authenticated_user'))
  
  def test_password_deactivated(self):
    user = _create_user(name='oink.hase')
    user.set_password('supergeheim')
    user.is_active=False
    db.session.commit()

    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': user.username, 'password': 'supergeheim' } )
      self.assertEqual(ret.status_code, 401)
      self.assertIsNone(g.get('authenticated_user'))


      

class TestTokenAuth(RouteBase):
  def test_token_status_no_token(self):
    ret = self.client.get('/v1/token-status')
    self.assertEqual(ret.status_code, 401)
  
  def test_token_status(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token='geheimschwein'))

    with self.app.test_client() as c:
      ret = c.get('/v1/token-status', headers={ 'Authorization': f"bearer {token_text}"})
      self.assertEqual(ret.status_code, 200)
      self.assertEqual(g.authenticated_user, user)
      self.assertDictEqual(ret.get_json(), { 'status': 'welcome' })

    with self.app.test_client() as c:
      ret = c.get('/v1/token-status', headers={ 'Authorization': f"Bearer {token_text}"})
      self.assertEqual(ret.status_code, 200)

    with self.app.test_client() as c:
      ret = c.get('/v1/token-status', headers={ 'Authorization': f"BEARER {token_text}"})
    self.assertEqual(ret.status_code, 200)
    

  def test_search_no_token(self):
    ret = self.client.get('/v1/search?value=grunz')
    self.assertEqual(ret.status_code, 401)

  def test_search_token(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token='geheimschwein'))

    with self.app.test_client() as c:
      ret = c.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
      self.assertEqual(ret.status_code, 200)
      self.assertEqual(g.authenticated_user, user)
  
  def test_invalid_token(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token='geheimschwein'))

    with self.app.test_client() as c:
      ret = c.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer oink{token_text}"})
      self.assertEqual(ret.status_code, 401)
      self.assertIsNone(g.authenticated_user)
  
  def test_invalid_header(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token='geheimschwein'))

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer"})
    self.assertEqual(ret.status_code, 406)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"{token_text}"})
    self.assertEqual(ret.status_code, 406)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"oink {token_text}"})
    self.assertEqual(ret.status_code, 406)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text} oink"})
    self.assertEqual(ret.status_code, 406)
  
  def test_deactivated(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token='geheimschwein'))
    user.is_active=False

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 401)
