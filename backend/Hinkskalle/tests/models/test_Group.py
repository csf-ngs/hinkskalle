from datetime import datetime, timedelta
from Hinkskalle.tests.model_base import ModelBase

from Hinkskalle.models import Group, GroupSchema

from Hinkskalle import db

def _create_group(name='Testhasenstall'):
  group = Group(name=name, email=name+'@ha.se')
  db.session.add(group)
  db.session.commit()
  return group

class TestGroup(ModelBase):

  def test_group(self):
    group = _create_group('Testhasenstall')
    db.session.add(group)
    db.session.commit()

    read_group = Group.query.filter_by(name='Testhasenstall').first()
    self.assertEqual(read_group.id, group.id)
    self.assertTrue(abs(read_group.createdAt - datetime.utcnow()) < timedelta(seconds=1))
  
  def test_schema(self):
    schema = GroupSchema()
    group = _create_group()

    serialized = schema.dump(group)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['id'], str(group.id))

    self.assertFalse(serialized.data['deleted'])
    self.assertIsNone(serialized.data['deletedAt'])
  
  def test_schema_users(self):
    schema = GroupSchema()
    from Hinkskalle.tests.models.test_User import _create_user
    user = _create_user()
    group = _create_group()
    group.users.append(user)
    db.session.commit()

    serialized = schema.dump(group)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['users'][0]['id'], str(user.id))




