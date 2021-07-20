import unittest
from Hinkskalle import db
import os
from fakeredis import FakeStrictRedis
from rq import Queue

from . import app

class JobBase(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
    os.environ['RQ_CONNECTION_CLASS']='fakeredis.FakeStrictRedis'
  
  def setUp(self):
    self.app = app
    self.queue = Queue(is_async=False, connection=FakeStrictRedis())
    self.app.config['TESTING']=True
    self.app.app_context().push()
    db.create_all()
  
  def tearDown(self):
    db.session.rollback()
    db.session.close()
    db.drop_all()
