from Hinkskalle.tests.model_base import ModelBase
from unittest import mock

from Hinkskalle.util.auth import PasswordAuthenticators
from Hinkskalle.util.auth.ldap import LDAPUsers
from Hinkskalle.util.auth.local import LocalUsers
from Hinkskalle.util.auth.exceptions import *

class TestAuth(ModelBase):

  def test_config(self):

    auth = PasswordAuthenticators()
    self.app.config['AUTH']={}

    auth.init_app(self.app)
    self.assertEqual(len(auth.checkers), 1)
    self.assertIsInstance(auth.checkers[0], LocalUsers)

    self.app.config['AUTH']['LDAP']={'HOST': 'oi.nk'}
    auth.init_app(self.app)
    self.assertEqual(len(auth.checkers), 2)
    self.assertIsInstance(auth.checkers[0], LDAPUsers)
    self.assertIsInstance(auth.checkers[1], LocalUsers)
  
  def test_check_local(self):
    auth = PasswordAuthenticators()
    self.app.config['AUTH']={}

    auth.init_app(self.app)
    with mock.patch.object(LocalUsers, 'check_password', return_value=True) as mock_check:
      auth.check_password('test.hase', 'oink')
    mock_check.assert_called_once_with('test.hase', 'oink')

    with mock.patch.object(LocalUsers, 'check_password', return_value=None) as mock_check:
      with self.assertRaises(UserNotFound):
        auth.check_password('test.hase', 'oink')
    
    with mock.patch.object(LocalUsers, 'check_password', side_effect=UserNotFound) as mock_check:
      with self.assertRaises(UserNotFound):
        auth.check_password('test.hase', 'oink')

    with mock.patch.object(LocalUsers, 'check_password', side_effect=UserDisabled) as mock_check:
      with self.assertRaises(UserDisabled):
        auth.check_password('test.hase', 'oink')

    with mock.patch.object(LocalUsers, 'check_password', side_effect=InvalidPassword) as mock_check:
      with self.assertRaises(InvalidPassword):
        auth.check_password('test.hase', 'oink')
