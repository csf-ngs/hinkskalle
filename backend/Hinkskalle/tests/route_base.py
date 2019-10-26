import unittest
import os
from unittest import mock
from flask import g
from contextlib import contextmanager

from Hinkskalle import create_app
from Hinkskalle.fsk_api import FskUser
from Hinkskalle.models import Entity, Collection, Container, Image, Tag

@contextmanager
def fake_admin_auth(app):
  fsk_admin_auth_mock = mock.patch('fsk_authenticator.FskAdminAuthenticator.authenticate')
  fsk_auth_mock = mock.patch('fsk_authenticator.FskAuthenticator.authenticate')
  fsk_admin_auth_mock.start()
  fsk_auth_mock.start()
  with app.app_context():
    g.fsk_user=FskUser('test.hase', True)
    yield
  fsk_admin_auth_mock.stop()
  fsk_auth_mock.stop()

@contextmanager
def fake_auth(app):
  fsk_auth_mock = mock.patch('fsk_authenticator.FskAuthenticator.authenticate')
  fsk_auth_mock.start()
  with app.app_context():
    g.fsk_user=FskUser('test.hase', False)
    yield
  fsk_auth_mock.stop()

class RouteBase(unittest.TestCase):
  app = None
  client = None

  @classmethod
  def setUpClass(cls):
    os.environ['MONGODB_HOST']='mongomock://localhost'
  
  def setUp(self):
    self.app = create_app()
    self.app.config['TESTING'] = True
    self.client = self.app.test_client()

  def tearDown(self):
    Entity.objects.delete()
    Collection.objects.delete()
    Container.objects.delete()
    Image.objects.delete()
    Tag.objects.delete()