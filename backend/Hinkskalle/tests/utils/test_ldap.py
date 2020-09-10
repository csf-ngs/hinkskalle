from Hinkskalle.tests.model_base import ModelBase
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_AD_2012_R2

from Hinkskalle.util.auth.ldap import LDAPUsers, LDAPService
from Hinkskalle.util.auth.exceptions import *

class TestLdap(ModelBase):
  def setUp(self):
    super().setUp()
    self.svc = None
  
  def _create_user(self, name='test.hase', password='supersecret', is_admin=False):
    self.svc.connection.strategy.add_entry(f"cn={name},ou=test", {'cn': name, 'userPassword': password})
    return { 'username': name, 'password': password }

  def _setup_mock(self):
    dummy_root = 'cn=root.hase,ou=test'
    dummy_password = 'dummy'

    if not self.svc:
      self.svc = LDAPService(host='dummy', port=None, bind_dn=dummy_root, bind_password=dummy_password, base_dn='ou=test', get_info=OFFLINE_AD_2012_R2, client_strategy=MOCK_SYNC)
      self.svc.connection.strategy.add_entry(f"cn=root.hase,ou=test", { 'cn': dummy_root, 'userPassword': dummy_password })
    auth = LDAPUsers()
    auth.ldap = self.svc
    return auth
    

  def test_check(self):
    auth = self._setup_mock()
    user = self._create_user()

    check_user = auth.check_password(user.get('username'), user.get('password'))

  def test_check_twice(self):
    auth = self._setup_mock()
    user = self._create_user()
    other_user = self._create_user(name='oink.hase')

    check_user = auth.check_password(user.get('username'), user.get('password'))
    check_other_user = auth.check_password(other_user.get('username'), other_user.get('password'))

  def test_not_found(self):
    auth = self._setup_mock()
    user = self._create_user()

    with self.assertRaises(UserNotFound):
      check_user = auth.check_password('someone', 'somesecret')

  def test_invalid_password(self):
    auth = self._setup_mock()
    user = self._create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('username'), user.get('password')+'oink')

  def test_invalid_password_recheck(self):
    auth = self._setup_mock()
    user = self._create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('username'), user.get('password')+'oink')
    
    # should work
    check_user = auth.check_password(user.get('username'), user.get('password'))
  
  def test_none_password(self):
    auth = self._setup_mock()
    user = self._create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('username'), None)

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('username'), '')

  
  def test_sync(self):
    auth = self._setup_mock()
    auth._sync_user({ 'attributes': { 'cn': 'test.hase' }})