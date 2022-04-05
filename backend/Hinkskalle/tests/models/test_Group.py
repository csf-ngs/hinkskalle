from datetime import datetime, timedelta
from ..model_base import ModelBase
from .._util import _create_group, _create_user

from Hinkskalle.models import Group, GroupSchema

from Hinkskalle import db

class TestGroup(ModelBase):

  def test_group(self):
    group = _create_group('Testhasenstall')
    db.session.add(group)
    db.session.commit()

    read_group = Group.query.filter_by(name='Testhasenstall').first()
    self.assertEqual(read_group.id, group.id)
    self.assertTrue(abs(read_group.createdAt - datetime.now()) < timedelta(seconds=1))
  
  def test_schema(self):
    schema = GroupSchema()
    group = _create_group()

    serialized = schema.dump(group)
    self.assertEqual(serialized['id'], str(group.id))

    self.assertFalse(serialized['deleted'])
    self.assertIsNone(serialized['deletedAt'])
  
  def test_schema_users(self):
    schema = GroupSchema()
    user = _create_user()
    group = _create_group()
    group.users.append(user)
    db.session.commit()

    serialized = schema.dump(group)
    self.assertEqual(serialized['users'][0]['id'], str(user.id))




