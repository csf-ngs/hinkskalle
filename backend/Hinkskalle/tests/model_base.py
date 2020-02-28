import unittest
from Hinkskalle import db, create_app
import os

class ModelBase(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
  
  def setUp(self):
    self.app = create_app()
    self.app.config['TESTING']=True
    self.app.app_context().push()
    db.create_all()
  
  def tearDown(self):
    db.drop_all()