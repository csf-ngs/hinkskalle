import unittest
import datetime
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
    self.assertIn('expiresAt', data)

    self.assertEqual(len(user.tokens), 1)
    db_token = Token.query.filter(Token.id==data['id']).first()
    self.assertIsNotNone(db_token)
    self.assertEqual(db_token.source, 'auto')
    self.assertTrue(abs(db_token.expiresAt - (datetime.datetime.now()+Token.defaultExpiration)) < datetime.timedelta(minutes=1))
  
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
    user.tokens.append(Token(token=token_text))

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
    user.tokens.append(Token(token=token_text))

    with self.app.test_client() as c:
      ret = c.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
      self.assertEqual(ret.status_code, 200)
      self.assertEqual(g.authenticated_user, user)
  
  def test_invalid_token(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token=token_text))

    with self.app.test_client() as c:
      ret = c.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer oink{token_text}"})
      self.assertEqual(ret.status_code, 401)
      self.assertIsNone(g.authenticated_user)
  
  def test_invalid_header(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    user.tokens.append(Token(token=token_text))

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
    user.tokens.append(Token(token=token_text))
    user.is_active=False

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 401)

  def test_deleted(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    token = Token(token=token_text, user=user)
    token.deleted = True
    user.tokens.append(token)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 401)
  
  def test_expired(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschwein'
    token = Token(token=token_text, user=user)
    token.expiresAt = datetime.datetime.now() - datetime.timedelta(weeks=1)
    user.tokens.append(token)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 401)
  
  def test_update_expiration_auto(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschein'
    token = Token(token=token_text, user=user, source='auto', expiresAt=datetime.datetime.now() + datetime.timedelta(hours=1))
    user.tokens.append(token)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 200)

    db_token = Token.query.get(token.id)
    self.assertLess(abs(db_token.expiresAt - (datetime.datetime.now()+Token.defaultExpiration)), datetime.timedelta(minutes=1))

  def test_update_expiration_manual(self):
    user = _create_user(name='test.hase')
    token_text = 'geheimschein'
    expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
    token = Token(token=token_text, user=user, source='manual', expiresAt=expiration)
    user.tokens.append(token)

    ret = self.client.get('/v1/search?value=grunz', headers={ 'Authorization': f"bearer {token_text}"})
    self.assertEqual(ret.status_code, 200)

    db_token = Token.query.get(token.id)
    self.assertEqual(db_token.expiresAt, expiration)
