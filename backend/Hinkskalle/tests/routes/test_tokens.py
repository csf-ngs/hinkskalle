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
  
  def test_update_noauth(self):
    ret = self.client.put(f"/v1/users/{self.username}/tokens/{self.user_token_id}", json={ 'some': 'thing' })
    self.assertEqual(ret.status_code, 401)
  
  def test_delete_noauth(self):
    ret = self.client.delete(f"/v1/users/{self.username}/tokens/{self.user_token_id}")
    self.assertEqual(ret.status_code, 401)

