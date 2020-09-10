from Hinkskalle.tests.model_base import ModelBase, _create_user
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
    db_user = auth._sync_user({ 'attributes': { 'cn': 'test.hase', 'mail': 'test@ha.se', 'givenName': 'Test', 'sn': 'Hase' }})
    self.assertEqual(db_user.username, 'test.hase')
    self.assertEqual(db_user.email, 'test@ha.se')
    self.assertEqual(db_user.firstname, 'Test')
    self.assertEqual(db_user.lastname, 'Hase')
    self.assertIsNotNone(db_user.id)
  
  def test_sync_existing(self):
    auth = self._setup_mock()
    user = _create_user()

    db_user = auth._sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname, 'sn': user.lastname }})
    self.assertEqual(db_user.id, user.id)
    self.assertEqual(db_user.firstname, user.firstname)
  
  def test_sync_update(self):
    auth = self._setup_mock()
    user = _create_user()

    db_user = auth._sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname+'oink', 'sn': user.lastname+'oink' }})
    self.assertEqual(db_user.id, user.id)
    self.assertEqual(db_user.firstname, user.firstname)
    self.assertEqual(db_user.lastname, user.lastname)