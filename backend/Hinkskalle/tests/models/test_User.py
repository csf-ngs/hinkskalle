from datetime import datetime, timedelta
from Hinkskalle.tests.model_base import ModelBase, _create_group, _create_user

from Hinkskalle.models import User, UserSchema, Group, Token, TokenSchema

from Hinkskalle import db

class TestUser(ModelBase):

  def test_user(self):
    user = _create_user('test.hase')
    db.session.add(user)
    db.session.commit()

    read_user = User.query.filter_by(username='test.hase').first()
    self.assertEqual(read_user.id, user.id)
    self.assertTrue(abs(read_user.createdAt - datetime.utcnow()) < timedelta(seconds=1))
    self.assertFalse(read_user.is_admin)
  
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
  
  def test_token(self):
    user = _create_user()
    token1 = Token(user=user, id='geheimhase')
    db.session.add(token1)
    db.session.commit()

    read_token = Token.query.get('geheimhase')
    self.assertEqual(read_token.user_id, user.id)
    self.assertEqual(read_token.user, user)

    read_user = User.query.filter_by(username=user.username).one()
    self.assertListEqual(read_user.tokens, [read_token])
  
  def test_password(self):
    user = _create_user()
    user.set_password('geheimhase')
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    self.assertNotEqual(read_user.password, 'geheimhase')

    self.assertTrue(read_user.check_password('geheimhase'))
    self.assertFalse(read_user.check_password('Falscher Hase'))
  
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
    token = Token(user=user, id='geheimhase')

    serialized = schema.dump(token)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['id'], 'geheimhase')
    self.assertEqual(serialized.data['user']['id'], str(user.id))
  
  def test_access(self):
    subject = _create_user()

    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')

    self.assertTrue(subject.check_access(try_admin))
    self.assertTrue(subject.check_access(try_normal))
  
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



