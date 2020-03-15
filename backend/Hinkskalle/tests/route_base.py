import unittest
import os
from unittest import mock
from flask import g
from contextlib import contextmanager

from Hinkskalle import create_app, db
from Hinkskalle.models import Entity, Collection, Container, Image, Tag, User

from Hinkskalle.tests.model_base import _create_user

class RouteBase(unittest.TestCase):
  app = None
  client = None

  @classmethod
  def setUpClass(cls):
    os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
  
  def setUp(self):
    self.app = create_app()
    self.app.config['TESTING'] = True
    self.app.config['DEBUG'] = True
    self.client = self.app.test_client()

    self.app.app_context().push()
    db.create_all()

    self.admin_username='admin.hase'
    self.admin_user = _create_user(name=self.admin_username, is_admin=True)
    self.username='user.hase'
    self.user = _create_user(name=self.username, is_admin=False)
    self.other_username='other.hase'
    self.other_user = _create_user(name=self.other_username, is_admin=False)

    # This is strange: The real before_request_func
    # gets executed only once. I guess it has something to do with using current_app??
    # anyways, this is a quick and dirty fix
    from Hinkskalle.routes import before_request_func
    @self.app.before_request
    def fake_before():
      return before_request_func()

  def tearDown(self):
    db.drop_all()

  @contextmanager
  def fake_auth(self):
    token_auth_mock = mock.patch('Hinkskalle.util.auth.TokenAuthenticator.authenticate')
    token_auth_mock.start()
    with self.app.app_context():
      # re-read user from database to ensure that it is in the context db session
      g.authenticated_user=User.query.filter(User.username==self.username).one()
      yield
    token_auth_mock.stop()

  @contextmanager
  def fake_admin_auth(self):
    token_auth_mock = mock.patch('Hinkskalle.util.auth.TokenAuthenticator.authenticate')
    token_auth_mock.start()
    with self.app.app_context():
      # re-read user from database to ensure that it is in the context db session
      g.authenticated_user=User.query.filter(User.username==self.admin_username).one()
      yield
    token_auth_mock.stop()

