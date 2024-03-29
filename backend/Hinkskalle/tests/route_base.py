import unittest
import os
from unittest import mock
from flask import g
from contextlib import contextmanager

from flask.app import Flask
from flask.testing import FlaskClient

from Hinkskalle import db
from Hinkskalle.models import User

from ._util import _create_user

from . import app

class RouteBase(unittest.TestCase):
  app: Flask
  client: FlaskClient

  @classmethod
  def setUpClass(cls):
    os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
    os.environ['RQ_CONNECTION_CLASS']='fakeredis.FakeStrictRedis'
  
  def setUp(self):
    self.app = app
    self.app.config['TESTING'] = True
    self.app.config['DEBUG'] = True
    self.app.config['DEFAULT_USER_QUOTA'] = 0
    self.app.config['DEFAULT_GROUP_QUOTA'] = 0
    self.app.config['SINGULARITY_FLAVOR'] = 'singularity'
    self.app.config['ENABLE_REGISTER'] = False
    self.app.testing = True
    self.client = self.app.test_client()

    self.app.app_context().push()
    db.create_all()

    self.admin_username='admin.hase'
    self.admin_user = _create_user(name=self.admin_username, is_admin=True)
    self.username='user.hase'
    self.user = _create_user(name=self.username, is_admin=False)
    self.other_username='other.hase'
    self.other_user = _create_user(name=self.other_username, is_admin=False)


  def tearDown(self):
    db.session.rollback()
    db.session.close()
    db.drop_all()

  @contextmanager
  def fake_auth(self):
    token_auth_mock = mock.patch('Hinkskalle.util.auth.token.TokenAuthenticator.authenticate')
    token_auth_mock.start()
    with self.app.app_context():
      # re-read user from database to ensure that it is in the context db session
      g.authenticated_user=User.query.filter(User.username==self.username).one()
      yield
    token_auth_mock.stop()

  @contextmanager
  def fake_admin_auth(self):
    token_auth_mock = mock.patch('Hinkskalle.util.auth.token.TokenAuthenticator.authenticate')
    token_auth_mock.start()
    with self.app.app_context():
      # re-read user from database to ensure that it is in the context db session
      g.authenticated_user=User.query.filter(User.username==self.admin_username).one()
      yield
    token_auth_mock.stop()

