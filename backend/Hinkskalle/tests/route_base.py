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
  fsk_admin_auth_mock.start()
  with app.app_context():
    g.fsk_user=FskUser('test.hase', True)
  yield
  fsk_admin_auth_mock.stop()
  with app.app_context():
    g.fsk_user=None

class RouteBase(unittest.TestCase):
  app = None
  client = None

  @classmethod
  def setUpClass(cls):
    os.environ['MONGODB_HOST']='mongomock://localhost'
  
  def setUp(self):
    self.app = create_app()
    self.client = self.app.test_client()

  def tearDown(self):
    Entity.objects.delete()
    Collection.objects.delete()
    Container.objects.delete()
    Image.objects.delete()
    Tag.objects.delete()