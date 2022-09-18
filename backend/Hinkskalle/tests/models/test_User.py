from datetime import datetime, timedelta
from pprint import pprint
import typing

from marshmallow import ValidationError
from ..model_base import ModelBase
from .._util import _create_group, _create_user, _create_container

from Hinkskalle.models import User, UserSchema, Group, GroupSchema, Container, UserGroup, GroupRoles

from Hinkskalle import db

class TestUser(ModelBase):

  def test_user(self):
    user = _create_user('test.hase')
    db.session.add(user)
    db.session.commit()

    read_user = User.query.filter_by(username='test.hase').first()
    self.assertEqual(read_user.id, user.id)
    self.assertTrue(abs(read_user.createdAt - datetime.now()) < timedelta(seconds=2))
    self.assertFalse(read_user.is_admin)
  
  def test_quota(self):
    user = _create_user('test.hase')
    user.quota = 999
    db.session.add(user)
    db.session.commit()

    read_user = User.query.filter_by(username='test.hase').first()
    self.assertEqual(read_user.quota, 999)
  
  def test_default_quota(self):
    old_default = self.app.config['DEFAULT_USER_QUOTA']
    self.app.config['DEFAULT_USER_QUOTA'] = 1234

    user = _create_user('test.hase')
    self.assertEqual(user.quota, self.app.config['DEFAULT_USER_QUOTA'])
    db.session.add(user)
    db.session.commit()

    read_user = User.query.filter_by(username='test.hase').first()
    self.assertEqual(user.quota, self.app.config['DEFAULT_USER_QUOTA'])

    self.app.config['DEFAULT_USER_QUOTA'] = old_default

  
  def test_username_check(self):
    with self.assertRaisesRegex(ValueError, r'name contains invalid'):
      User(username='bl^a&*.h@ase', email='test@testha.se', firstname='Bla', lastname='Hase')

  
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
    group1_opt = UserGroup(group=group1, user=user, role=GroupRoles.contributor)

    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_group = Group.query.filter_by(name=group1.name).one()

    self.assertListEqual([ m.group for m in read_user.groups], [read_group])
    self.assertListEqual([ m.user for m in read_group.users], [read_user])

    db.session.delete(group1_opt)
    db.session.commit()

    read_user = User.query.filter_by(username=user.username).one()
    read_group = Group.query.filter_by(name=group1.name).one()
    self.assertListEqual(read_user.groups, [])
    self.assertListEqual(read_group.users, [])
  
  def test_group_default_quota(self):
    old_default = self.app.config['DEFAULT_GROUP_QUOTA']
    self.app.config['DEFAULT_GROUP_QUOTA'] = 1234
    group = _create_group('Testhase2')
    self.assertEqual(group.quota, self.app.config['DEFAULT_GROUP_QUOTA'])
    db.session.add(group)
    db.session.commit()

    read_group = Group.query.filter_by(name='Testhase2').one()
    self.assertEqual(group.quota, self.app.config['DEFAULT_GROUP_QUOTA'])

    self.app.config['DEFAULT_GROUP_QUOTA'] = old_default
  
  def test_group_quota(self):
    group = _create_group('Testhase2')
    group.quota = 666
    db.session.add(group)
    db.session.commit()

    read_group = Group.query.filter_by(name='Testhase2').one()
    self.assertEqual(read_group.quota, 666)


  
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
  
  
  def test_schema(self):
    schema = UserSchema()
    user = _create_user()
    user.quota = 999

    serialized = typing.cast(dict, schema.dump(user))
    self.assertEqual(serialized['id'], str(user.id))
    self.assertEqual(serialized['username'], user.username)
    self.assertFalse(serialized['isAdmin'])
    self.assertTrue(serialized['isActive'])

    self.assertFalse(serialized['deleted'])
    self.assertIsNone(serialized['deletedAt'])

    self.assertNotIn('tokens', serialized)
    self.assertNotIn('password', serialized)

    self.assertEqual(serialized['quota'], user.quota)

    user.is_admin=True
    serialized = typing.cast(dict, schema.dump(user))
    self.assertTrue(serialized['isAdmin'])
    self.assertTrue(serialized['isActive'])

  def test_group_schema(self):
    schema = GroupSchema()
    group = _create_group()
    group.quota = 999

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['quota'], group.quota)
  
  def test_group_deserialize(self):
    schema = GroupSchema()
    deserialized = typing.cast(dict, schema.load({
      'name': 'Testhasenstall',
      'email': 'testhase@testha.se',
      'quota': 666
    }))
    self.assertEqual(deserialized['quota'], 666)

  def test_deserialize(self):
    schema = UserSchema()

    deserialized = typing.cast(dict, schema.load({
      'username':'test.hase', 
      'email': 'test@ha.se',
      'firstname': 'Test',
      'lastname': 'Hase',
      'isAdmin': True,
      'isActive': True,
      'quota': 999,
    }))
    self.assertTrue(deserialized['is_admin'])
    self.assertTrue(deserialized['is_active'])
    self.assertEqual(deserialized['quota'], 999)
  
  def test_deserialize_username_check(self):
    schema = UserSchema()
    with self.assertRaisesRegex(ValidationError, r'username'):
      deserialized = schema.load({
        'username': 't@st.h@ase',
        'email': 'test@ha.se',
        'firstname': 'Test',
        'lastname': 'Hase',
        'isAdmin': True
      })


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
    group_schema = GroupSchema()
    user = _create_user()
    group = _create_group()
    group_m = UserGroup(user=user, group=group, role=GroupRoles.contributor)
    db.session.add(group_m)
    db.session.commit()

    serialized = typing.cast(dict, schema.dump(user))
    self.assertEqual(serialized['groups'][0]['group']['id'], str(group.id))

    serialized = typing.cast(dict, group_schema.dump(group))
    self.assertEqual(serialized['users'][0]['user']['id'], str(user.id))
  