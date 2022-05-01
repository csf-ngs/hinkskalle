from Hinkskalle.models.User import Token
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests._util import _create_user

from Hinkskalle import db

import base64

class TestOrasAuth(RouteBase):
  # no extensive tests for account status etc.
  # this should be covered in unit tests for the
  # authenticators used here.

  def test_get_base_with_auth(self):
    with self.fake_admin_auth():
      ret = self.client.get('/v2/')
    self.assertEqual(ret.status_code, 200)
  
  def test_get_base_no_auth(self):
    ret = self.client.get('/v2/')
    self.assertEqual(ret.status_code, 401)
    auth_header = ret.headers.get('WWW-Authenticate', '')
    self.assertRegexpMatches(auth_header, '^bearer ')
  
  def test_get_base_basic_auth(self):
    user = _create_user('oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    auth_data = base64.b64encode(f'{user.username}:supergeheim'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'basic {auth_data}'})
    self.assertEqual(ret.status_code, 200)
    token_data = ret.get_json()
    self.assertIn('access_token', token_data)
    token = token_data['access_token'] # type: ignore
    db_token = Token.query.filter(Token.key_uid==token[:12]).first()
    self.assertIsNotNone(db_token)

  def test_get_base_basic_auth_wrong_password(self):
    user = _create_user('oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    auth_data = base64.b64encode(f'{user.username}:supergeheimschwein'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'basic {auth_data}'})
    self.assertEqual(ret.status_code, 401)

  def test_get_base_basic_auth_wrong_username(self):
    user = _create_user('oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    auth_data = base64.b64encode(f'{user.username}schwein:supergeheimschwein'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'basic {auth_data}'})
    self.assertEqual(ret.status_code, 401)

  def test_get_base_basic_auth_no_password(self):
    user = _create_user('oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    auth_data = base64.b64encode(f'{user.username}:'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'basic {auth_data}'})
    self.assertEqual(ret.status_code, 401)

    auth_data = base64.b64encode(f'{user.username}'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'basic {auth_data}'})
    self.assertEqual(ret.status_code, 401)

  def test_get_base_basic_auth_wrong_scheme(self):
    user = _create_user('oink.hase')
    user.set_password('supergeheim')
    db.session.commit()

    auth_data = base64.b64encode(f'{user.username}:supergeheim'.encode('utf8')).decode('utf8')
    ret = self.client.get('/v2/', headers={'Authorization': f'complicated {auth_data}'})
    self.assertEqual(ret.status_code, 406)
  
  def test_post_base_empty(self):
    ret = self.client.post('/v2/')
    self.assertEqual(ret.status_code, 401)

  def test_post_base_no_token(self):
    ret = self.client.post('/v2/', data={'some': 'thing'})
    self.assertEqual(ret.status_code, 401)

  def test_post_base_invalid_token(self):
    ret = self.client.post('/v2/', data={'refresh_token': 'oink'})
    self.assertEqual(ret.status_code, 401)

  def test_post_base(self):
    user = _create_user('oink.hase')
    token = Token(token='oinkoinkoinkoink', user_id=user.id)
    db.session.add(token)
    db.session.commit()
    db.session.expunge_all()
    ret = self.client.post('/v2/', data={'refresh_token': 'oinkoinkoinkoink'})
    self.assertEqual(ret.status_code, 200)

    token_data = ret.get_json()
    self.assertIn('access_token', token_data)
    token = token_data['access_token'] # type: ignore
    self.assertEqual(token, 'oinkoinkoinkoink')