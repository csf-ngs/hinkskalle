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

  
  def test_schema(self):
    schema = GroupSchema()
    group = _create_group()

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['id'], str(group.id))

    self.assertIsNone(serialized['entity_ref'])

    self.assertFalse(serialized['deleted'])
    self.assertIsNone(serialized['deletedAt'])

    entity = Entity(name='oinkstall', group=group)
    db.session.add(entity)

    serialized = typing.cast(dict, schema.dump(group))
    self.assertEqual(serialized['entity_ref'], entity.name)


  
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




