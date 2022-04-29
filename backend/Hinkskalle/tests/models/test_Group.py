from datetime import datetime, timedelta
from pprint import pprint
import typing

from sqlalchemy.exc import IntegrityError

from ..model_base import ModelBase
from .._util import _create_group, _create_user

from Hinkskalle.models import Group, GroupSchema, GroupRoles, UserGroup, Entity

from Hinkskalle import db

class TestGroup(ModelBase):

  def test_group(self):
    group = _create_group('Testhasenstall')
    db.session.add(group)
    db.session.commit()

    read_group = Group.query.filter_by(name='Testhasenstall').first()
    self.assertEqual(read_group.id, group.id)
    self.assertTrue(abs(read_group.createdAt - datetime.now()) < timedelta(seconds=2))
  
  def test_entity(self):
    group = _create_group('Testhasentall')

    entity = Entity(name='testhasenstall', group=group)
    db.session.add(entity)
    db.session.commit()

    self.assertEqual(group.entity.name, 'testhasenstall')
  
    with self.assertRaises(IntegrityError):
      entity2 = Entity(name='oinkhasenstall', group_id=group.id)
      db.session.add(entity2)
      db.session.commit()

    db.session.rollback()
    self.assertEqual(group.entity.name, 'testhasenstall')

  def test_access(self):
    subject = _create_group()
    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')
    try_other = _create_user('other.hase')

    self.assertTrue(subject.check_access(try_admin))
    self.assertFalse(subject.check_access(try_normal))
    self.assertFalse(subject.check_access(try_other))

    ug = UserGroup(user=try_normal, group=subject)
    db.session.add(ug)
    db.session.commit()

    self.assertTrue(subject.check_access(try_normal))
    self.assertFalse(subject.check_access(try_other))
  
  def test_access_owner(self):
    try_normal = _create_user('normal.hase', is_admin=False)
    subject = _create_group()

    self.assertFalse(subject.check_access(try_normal))
    subject.owner=try_normal
    self.assertTrue(subject.check_access(try_normal))
  
  def test_update_access(self):
    subject = _create_group()
    try_admin = _create_user('admin.hase', is_admin=True)
    try_normal = _create_user('normal.hase')

    self.assertTrue(subject.check_update_access(try_admin))
    self.assertFalse(subject.check_update_access(try_normal))

    ug = UserGroup(user=try_normal, group=subject)
    db.session.add(ug)
    db.session.commit()
    for allow in [ GroupRoles.admin ]:
      ug.role = allow
      db.session.commit()
      self.assertTrue(subject.check_update_access(try_normal))
    for deny in [ GroupRoles.contributor, GroupRoles.readonly ]:
      ug.role = deny
      db.session.commit()
      self.assertFalse(subject.check_update_access(try_normal))

  def test_update_access_owner(self):
    subject = _create_group()
    try_normal = _create_user('normal.hase', is_admin=False)
    self.assertFalse(subject.check_update_access(try_normal))

    subject.owner=try_normal
    self.assertTrue(subject.check_update_access(try_normal))



  
  def test_schema(self):
    schema = GroupSchema()
    group = _create_group()

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['id'], str(group.id))

    self.assertIsNone(serialized['entityRef'])

    self.assertFalse(serialized['deleted'])
    self.assertIsNone(serialized['deletedAt'])

  def test_schema_entity(self):
    schema = GroupSchema()
    group = _create_group()
    entity = Entity(name='testhasenstall', group=group)
    db.session.add(entity)
    db.session.commit()

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['entityRef'], entity.name)


  
  def test_schema_users(self):
    schema = GroupSchema()
    user = _create_user()
    group = _create_group()
    group.users.append(UserGroup(user=user, group=group, role=GroupRoles.readonly))
    db.session.commit()

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['users'][0]['user']['id'], str(user.id))
    self.assertEqual(serialized['users'][0]['user']['username'], user.username) 
    self.assertEqual(serialized['users'][0]['role'], str(GroupRoles.readonly))

  def test_deserialize(self):
    schema = GroupSchema()

    deserialized = typing.cast(dict, schema.load({
      'name': 'Testhasenstall',
      'email': 'test@ha.se',
    }))
    self.assertEqual(deserialized['name'], 'Testhasenstall')
  