from ..route_base import RouteBase
from .._util import _create_user

from Hinkskalle.models.User import Token
from Hinkskalle import db

import datetime
import typing

class TestTokens(RouteBase):
  def setUp(self):
    super().setUp()
    self.user_token = Token(token='geheimes-geheimnis')
    self.user.tokens.append(self.user_token)
    db.session.commit()
    self.user_token_id = self.user_token.id

  def test_list_noauth(self):
    ret = self.client.get(f"/v1/users/{self.username}/tokens")
    self.assertEqual(ret.status_code, 401)
  
  def test_create_noauth(self):
    ret = self.client.post(f"/v1/users/{self.username}/tokens", json={ 'some': 'thing' })
    self.assertEqual(ret.status_code, 401)
  
  def test_delete_noauth(self):
    ret = self.client.delete(f"/v1/users/{self.username}/tokens/{self.user_token_id}")
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    self.user_token.source='manual'
    db.session.commit()
    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{self.username}/tokens")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIsInstance(json, list)
    self.assertListEqual([ t['id'] for t in json ], [ str(self.user_token_id) ])

  def test_list_no_auto(self):
    self.user_token.source='auto'
    db.session.commit()
    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{self.username}/tokens")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIsInstance(json, list)
    self.assertListEqual([ t['id'] for t in json ], [ ])

  def test_list_other(self):
    other_token = Token(token='geheimkatze', user=self.other_user)
    db.session.add(other_token)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{self.other_username}/tokens")
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{self.other_username}/tokens")
    self.assertEqual(ret.status_code, 200)
  
  def test_create(self):
    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{self.username}/tokens", json={})
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertNotIn('token', json)
    self.assertGreater(len(json['generatedToken']), 32)
    gen_uid = typing.cast(str, json['generatedToken'])[:12]
    self.assertEqual(json['key_uid'], gen_uid)

    db_token = Token.query.filter(Token.key_uid == json['key_uid']).first()
    self.assertIsNotNone(db_token)
    self.assertEqual(db_token.source, 'manual')
  
  def test_create_attrs(self):
    now = datetime.datetime.now()
    post = { 'comment': 'This token will self-destruct in 60 seconds', 'expiresAt': now.isoformat() }
    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{self.username}/tokens", json=post)
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertEqual(json['comment'], post['comment'])

    db_token = Token.query.filter(Token.key_uid == json['key_uid']).first()
    self.assertIsNotNone(db_token)
    self.assertEqual(db_token.comment, post['comment'])
    self.assertEqual(db_token.expiresAt, now)

  
  def test_create_other(self):
    user = _create_user('schlumpf.hase')

    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{user.username}/tokens", json={})
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/users/{user.username}/tokens", json={})
    self.assertEqual(ret.status_code, 200)
  
  def test_update(self):
    now = datetime.datetime.now()
    post = {
      'comment': 'oink',
      'expiresAt': now.isoformat(),
    }
    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.username}/tokens/{self.user_token_id}", json=post)
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertEqual(json['comment'], post['comment'])

    db_token = Token.query.filter(Token.key_uid == json['key_uid']).first()
    self.assertIsNotNone(db_token)
    self.assertEqual(db_token.comment, post['comment'])
    self.assertEqual(db_token.expiresAt, now)
  
  def test_update_other(self):
    new_token = Token(token='auch geheim', user=self.other_user)
    db.session.add(new_token)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/users/{self.other_username}/tokens/{new_token.id}", json={"comment": "something"})
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/users/{self.other_username}/tokens/{new_token.id}", json={"comment": "something"})
    self.assertEqual(ret.status_code, 200)


  
  def test_delete(self):
    new_token = Token(token='Ken sent me', user=self.user)
    db.session.add(new_token)
    db.session.commit()
    new_uid = new_token.key_uid
    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.user.username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Token.query.filter(Token.key_uid==new_uid).first())
  
  def test_delete_other(self):
    new_token = Token(token='Ken sent me', user=self.other_user)
    db.session.add(new_token)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.other_username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/users/{self.other_username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 200)


  
