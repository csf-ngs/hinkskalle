import unittest
from Hinkskalle import db, create_app
from Hinkskalle.models import User, Group
import os
from . import app

def _create_user(name='test.hase', is_admin=False):
  firstname, lastname = name.split('.')
  user = User(username=name, email=name+'@ha.se', firstname=firstname, lastname=lastname, is_admin=is_admin)
  db.session.add(user)
  db.session.commit()
  return user

def _create_group(name='Testhasenstall'):
  group = Group(name=name, email=name+'@ha.se')
  db.session.add(group)
  db.session.commit()
  return group



class ModelBase(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
    os.environ['RQ_CONNECTION_CLASS']='fakeredis.FakeStrictRedis'
  
  def setUp(self):
    self.app = app
    self.app.config['TESTING']=True
    self.app.app_context().push()
    db.create_all()
  
  def tearDown(self):
    db.session.rollback()
    db.session.close()
    db.drop_all()