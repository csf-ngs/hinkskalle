import unittest
from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests.model_base import _create_user

from Hinkskalle.models import User, Token
from Hinkskalle import db

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
    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{self.username}/tokens")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIsInstance(json, list)
    self.assertListEqual([ t['id'] for t in json ], [ str(self.user_token_id) ])

  def test_list_other(self):
    other_token = Token(token='geheimkatze', user=self.other_user)
    db.session.add(other_token)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/users/{self.other_username}/tokens")
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/users/{self.other_username}/tokens")
    self.assertEqual(ret.status_code, 403)
  
  def test_create(self):
    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{self.username}/tokens", json={})
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertGreater(len(json['token']), 32)

    db_token = Token.query.filter(Token.token == json['token']).first()
    self.assertIsNotNone(db_token)
  
  def test_create_other(self):
    user = _create_user('schlumpf.hase')

    with self.fake_auth():
      ret = self.client.post(f"/v1/users/{user.username}/tokens", json={})
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/users/{user.username}/tokens", json={})
    self.assertEqual(ret.status_code, 403)
  
  def test_delete(self):
    new_token = Token(token='Ken sent me', user=self.user)
    db.session.add(new_token)
    db.session.commit()
    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.user.username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Token.query.filter(Token.token=='Ken sent me').first())
  
  def test_delete_other(self):
    new_token = Token(token='Ken sent me', user=self.other_user)
    db.session.add(new_token)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/users/{self.other_username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 403)

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/users/{self.other_username}/tokens/{new_token.id}")
    self.assertEqual(ret.status_code, 403)


  
