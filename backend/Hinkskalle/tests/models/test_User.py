from datetime import datetime, timedelta
from ..model_base import ModelBase
from .._util import _create_group, _create_user, _create_container

from Hinkskalle.models import User, UserSchema, Group, Token, TokenSchema, Container

from Hinkskalle import db

class TestUser(ModelBase):

  def test_user(self):
    user = _create_user('test.hase')
    db.session.add(user)
    db.session.commit()

    read_user = User.query.filter_by(username='test.hase').first()
    self.assertEqual(read_user.id, user.id)
    self.assertTrue(abs(read_user.createdAt - datetime.now()) < timedelta(seconds=1))
    self.assertFalse(read_user.is_admin)
  
  def test_user_case(self):
    user = _create_user('tEst.Hase')
    user.email = 'tEst@hA.Se'
    db.session.add(user)
    db.session.commit()

    dbUser = User.query.get(user.id)
    self.assertEqual(dbUser.username, 'test.hase')
    self.assertEqual(dbUser.email, 'test@ha.se')
  
  def test_group(self):
    user = _create_user()
    group1 = _create_group('Testhase1')

    user.groups.append(group1)
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_group = Group.query.filter_by(name=group1.name).one()

    self.assertListEqual(read_user.groups, [read_group])

    self.assertListEqual(read_group.users, [read_user])

    read_user.groups.remove(read_group)
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_group = Group.query.filter_by(name=group1.name).one()
    self.assertListEqual(read_user.groups, [])
    self.assertListEqual(read_group.users, [])
  
  def test_stars(self):
    user = _create_user()
    container = _create_container()[0]

    user.starred.append(container)
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_container = Container.query.filter_by(id=container.id).one()
    self.assertListEqual(read_user.starred, [read_container])
    self.assertListEqual(read_container.starred, [read_user])

    self.assertEqual(read_container.stars, 1)

    user.starred.append(read_container)
    db.session.commit()
    read_user = User.query.filter_by(username=user.username).one()
    read_container = Container.query.filter_by(id=container.id).one()
    self.assertListEqual(read_user.starred, [read_container])
    self.assertEqual(read_container.stars, 1)

    read_user.starred.remove(read_container)
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_container = Container.query.filter_by(id=container.id).one()
    self.assertListEqual(read_user.starred, [])
    self.assertListEqual(read_container.starred, [])
    self.assertEqual(read_container.stars, 0)

  
  def test_token(self):
    user = _create_user()
    token1 = Token(user=user, token='geheimhase')
    db.session.add(token1)
    db.session.commit()

    read_token = Token.query.filter(Token.token=='geheimhase').one()
    self.assertEqual(read_token.user_id, user.id)
    self.assertEqual(read_token.user, user)

    read_user = User.query.filter_by(username=user.username).one()
    self.assertListEqual(read_user.tokens, [read_token])
  
  def test_generate_token(self):
    user = _create_user()
    token1 = user.create_token()
    
    self.assertGreater(len(token1.token), 32)
    self.assertEqual(token1.user_id, user.id)
    self.assertListEqual(user.tokens, [token1])
  
  def test_password(self):
    user = _create_user()
    user.set_password('geheimhase')
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    self.assertNotEqual(read_user.password, 'geheimhase')

    self.assertTrue(read_user.check_password('geheimhase'))
    self.assertFalse(read_user.check_password('Falscher Hase'))
  
  def test_password_none(self):
    user = _create_user()
    self.assertFalse(user.check_password('irgendwas'))

    user.password = 'something'
    db.session.commit()
    self.assertFalse(user.check_password('something'))
  
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


  
  def test_schema(self):
    schema = UserSchema()
    user = _create_user()

    serialized = schema.dump(user)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['id'], str(user.id))
    self.assertEqual(serialized.data['username'], user.username)
    self.assertFalse(serialized.data['isAdmin'])

    self.assertFalse(serialized.data['deleted'])
    self.assertIsNone(serialized.data['deletedAt'])

    self.assertNotIn('tokens', serialized.data)
    self.assertNotIn('password', serialized.data)

    user.is_admin=True
    serialized = schema.dump(user)
    self.assertTrue(serialized.data['isAdmin'])

  def test_deserialize(self):
    schema = UserSchema()

    deserialized = schema.load({
      'username':'test.hase', 
      'email': 'test@ha.se',
      'firstname': 'Test',
      'lastname': 'Hase'
    })

    self.assertDictEqual(deserialized.errors, {})

  def test_schema_token(self):
    schema = TokenSchema()
    user = _create_user()
    token = Token(user=user, token='geheimhase')

    serialized = schema.dump(token)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['token'], 'geheimhase')
    self.assertEqual(serialized.data['user']['id'], str(user.id))
  
  def test_access(self):
    subject = _create_user()

    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')

    self.assertTrue(subject.check_access(try_admin))
    self.assertTrue(subject.check_access(try_normal))

  def test_sub_access(self):
    subject = _create_user()

    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')

    self.assertTrue(subject.check_sub_access(try_admin))
    self.assertFalse(subject.check_sub_access(try_normal))
    self.assertTrue(subject.check_sub_access(subject))
  
  def test_update_access(self):
    subject = _create_user()

    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')

    self.assertTrue(subject.check_update_access(try_admin))
    self.assertFalse(subject.check_update_access(try_normal))
    self.assertTrue(subject.check_update_access(subject))

  def test_schema_groups(self):
    schema = UserSchema()
    user = _create_user()
    group = _create_group()
    user.groups.append(group)
    db.session.commit()

    serialized = schema.dump(user)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['groups'][0]['id'], str(group.id))



