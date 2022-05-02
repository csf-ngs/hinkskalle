import typing

from Hinkskalle.models import Token, User, TokenSchema
from Hinkskalle import db

from ..model_base import ModelBase
from .._util import _create_user

class TestToken(ModelBase):
  def test_token(self):
    user = _create_user()
    token1 = Token(user=user, token='geheimhase012-geheimhase')
    db.session.add(token1)
    db.session.commit()
    
    read_token = Token.query.filter(Token.key_uid=='geheimhase01').one()
    self.assertEqual(read_token.user_id, user.id)
    self.assertEqual(read_token.user, user)
    self.assertNotEqual(read_token.token, 'geheimhase012-geheimhase')

    read_user = User.query.filter_by(username=user.username).one()
    self.assertListEqual(read_user.tokens, [read_token])
  
  def test_token_verify(self):
    user = _create_user()
    secret = 'geheimhase012-geheimhase'
    token1 = Token(user=user, token=secret)
    self.assertTrue(token1.check_token(secret))
    self.assertFalse(token1.check_token(None)) # type: ignore
    self.assertFalse(token1.check_token(''))
    self.assertFalse(token1.check_token(secret+'oink'))

    token1.token = None # type: ignore
    self.assertFalse(token1.check_token(secret))
    self.assertFalse(token1.check_token(None)) # type: ignore

  
  def test_generate_token(self):
    user = _create_user()
    token1 = user.create_token()
    
    self.assertGreater(len(token1.generatedToken), 32)
    self.assertNotEqual(token1.token, token1.generatedToken)
    self.assertEqual(token1.key_uid, token1.generatedToken[:12])
    self.assertEqual(token1.user_id, user.id)
    self.assertListEqual(user.tokens, [token1])
  
  def test_user_tokens(self):
    user = _create_user()
    token1 = Token(token='geheim')
    token2 = Token(token='auchgeheim')
    user.tokens = [ token1, token2 ]

    self.assertTrue(len(user.tokens)==2)
    self.assertTrue(len(user.manual_tokens)==0)

    token1.source='manual'
    db.session.commit()
    self.assertListEqual([ t.id for t in user.manual_tokens ], [ token1.id ])

  def test_schema_token(self):
    schema = TokenSchema()
    user = _create_user()
    token = Token(user=user, token='geheimhase')

    serialized = typing.cast(dict, schema.dump(token))
    self.assertNotIn('token', serialized)
    self.assertEqual(serialized['key_uid'], token.key_uid)
    self.assertEqual(serialized['user']['id'], str(user.id))
  
