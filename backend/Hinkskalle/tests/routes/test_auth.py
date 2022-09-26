import datetime
from flask import g
from ..route_base import RouteBase

from .._util import _create_user
from Hinkskalle.models.User import Token, PassKey
from Hinkskalle.models.Entity import Entity
from Hinkskalle import db
import re
import jwt
import base64

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

    data = ret.get_json().get('data') # type: ignore
    self.assertIn('id', data)
    self.assertIn('generatedToken', data)
    self.assertIn('expiresAt', data)

    self.assertEqual(len(user.tokens), 1)
    db_token = Token.query.filter(Token.id==data['id']).first()
    self.assertIsNotNone(db_token)
    self.assertEqual(db_token.source, 'auto')
    self.assertTrue(abs(db_token.expiresAt - (datetime.datetime.now()+Token.defaultExpiration)) < datetime.timedelta(minutes=1))
  
  def test_login_entity_create(self):
    user = _create_user(name='oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': user.username, 'password': 'supergeheim' } )
      self.assertEqual(ret.status_code, 200)
    db_entity = Entity.query.filter(Entity.name=='oink.hase').first()
    self.assertIsNotNone(db_entity)
    self.assertEqual(db_entity.createdBy, 'oink.hase')

  def test_login_entity_exists(self):
    user = _create_user(name='oink.hase')
    user.set_password('supergeheim')
    entity = Entity(name='oink.hase')
    db.session.add(entity)
    db.session.commit()
    entity_id=entity.id

    with self.app.test_client() as c:
      ret = c.post('/v1/get-token', json={ 'username': user.username, 'password': 'supergeheim' } )
      self.assertEqual(ret.status_code, 200)

  
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
  


class TestDownloadToken(RouteBase):
  def test_get_download_token(self):
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1' })
    self.assertEqual(ret.status_code, 202)
    data = ret.get_json()
    location = ret.headers.get('Location', '')
    self.assertTrue(location.endswith(data['location'])) # type: ignore
    temp_token = re.search(r'(.*)\?temp_token=(.*)', location)
    self.assertIsNotNone(temp_token)
    self.assertIsNotNone(temp_token[1])
    self.assertTrue(temp_token[1].endswith('/manifests/1/download'))
    self.assertIsNotNone(temp_token[2])
    decoded = jwt.decode(temp_token[2], self.app.config['SECRET_KEY'], algorithms=["HS256"])
    self.assertEqual(decoded.get('id'), '1')
    self.assertEqual(decoded.get('type'), 'manifest')
    self.assertEqual(decoded.get('username'), self.admin_username)
    self.assertLessEqual(decoded.get('exp'), int(datetime.datetime.now().timestamp()+self.app.config['DOWNLOAD_TOKEN_EXPIRATION']))
    self.assertGreaterEqual(decoded.get('exp'), int(datetime.datetime.now().timestamp()+self.app.config['DOWNLOAD_TOKEN_EXPIRATION']))
  
  def test_get_handout_token(self):
    override_exp = datetime.datetime.now().timestamp()+120
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1', 'username': self.username, 'exp': override_exp })
    self.assertEqual(ret.status_code, 202)
    location = ret.headers.get('Location', '')
    self.assertTrue(location.endswith(ret.get_json()['location']))  # type: ignore
    temp_token = re.search(r'(.*)\?temp_token=(.*)', location)
    decoded = jwt.decode(temp_token[2], self.app.config['SECRET_KEY'], algorithms=["HS256"])

    self.assertEqual(decoded.get('username'), self.username)
    self.assertEqual(decoded.get('exp'), int(override_exp))

  #OINK:
  def test_get_download_token_user(self):
    with self.fake_auth(): 
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1' })
    self.assertEqual(ret.status_code, 202)

  def test_get_download_token_user_no_override(self):
    with self.fake_auth():
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1', 'username': self.other_username })
    self.assertEqual(ret.status_code, 403)

    with self.fake_auth():
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1', 'exp': 4711 })
    self.assertEqual(ret.status_code, 403)

  def test_get_download_noauth(self):
    ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'manifest', 'id': '1' })
    self.assertEqual(ret.status_code, 401)

  def test_get_download_token_invalid_type(self):
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/get-download-token", json={ 'type': 'oink', 'id': '1' })
    self.assertEqual(ret.status_code, 406)


      

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
      self.assertEqual(ret.get_json().get('status'), 'welcome') # type: ignore
      json_user = ret.get_json().get('data') # type: ignore
      self.assertEqual(json_user.get('username'), 'test.hase')

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

class TestWebAuthn(RouteBase):
  def test_create_options(self):
    with self.fake_auth():
      ret = self.client.get('/v1/webauthn/create-options')
    self.assertEqual(ret.status_code, 200)
    opts = ret.get_json().get('data')
    self.assertEqual(opts['publicKey']['user']['name'], self.username)
    self.assertEqual(opts['publicKey']['user']['id'], self.user.passkey_id)

    self.assertEqual(opts['publicKey']['rp']['id'], 'localhost')
  
  def test_create_options_hostname(self):
    old_backend_url = self.app.config['BACKEND_URL']
    self.app.config['BACKEND_URL'] = 'https://oi.nk:1234/'

    with self.fake_auth():
      ret = self.client.get('/v1/webauthn/create-options')
    self.assertEqual(ret.status_code, 200)

    opts = ret.get_json().get('data')
    self.assertEqual(opts['publicKey']['rp']['id'], 'oi.nk')
    self.app.config['BACKEND_URL'] = old_backend_url
  
  def test_create_options_exclude(self):
    with self.fake_auth():
      ret = self.client.get('/v1/webauthn/create-options')
    self.assertEqual(ret.status_code, 200)

    opts = ret.get_json().get('data')
    self.assertListEqual(opts['publicKey']['excludeCredentials'], [])
  
  def test_create_options_exclude_has_key(self):
    passkey_id = b'4711'
    self.user.passkeys = [
      PassKey(id=passkey_id)
    ]
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get('/v1/webauthn/create-options')
    self.assertEqual(ret.status_code, 200)
    opts = ret.get_json().get('data')
    self.assertListEqual(
      opts['publicKey']['excludeCredentials'], [ 
        { 'type': 'public-key', 'id': base64.b64encode(passkey_id).decode('utf-8') }
      ])