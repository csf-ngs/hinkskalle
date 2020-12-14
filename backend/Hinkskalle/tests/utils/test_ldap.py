from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase, _create_user
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_AD_2012_R2

from Hinkskalle.util.auth.ldap import LDAPUsers, LDAPService
from Hinkskalle.util.auth.exceptions import *

class MockLDAP():
  dummy_root = 'cn=root.hase,ou=test'
  dummy_password = 'dummy'

  def __init__(self):
    self.svc = LDAPService(host='dummy', port=None, bind_dn=self.dummy_root, bind_password=self.dummy_password, base_dn='ou=test', get_info=OFFLINE_AD_2012_R2, client_strategy=MOCK_SYNC)
    self.svc.connection.strategy.add_entry(f"cn=root.hase,ou=test", { 'cn': self.dummy_root, 'userPassword': self.dummy_password })

    self.auth = LDAPUsers()
    self.auth.ldap = self.svc
  
  def create_user(self, name='test.hase', password='supersecret', is_admin=False):
    create_user = { 'cn': name, 'userPassword': password, 'mail': f"{name}@testha.se", 'sn': 'Oink', 'givenName': 'Grunz' }
    # add_entry seems to mutate the dict (all values turn to lists)
    self.svc.connection.strategy.add_entry(f"cn={name},ou=test", create_user.copy())
    return create_user


class TestLdap(ModelBase):

  def _setup_mock(self):
    self.mock = MockLDAP()
    return self.mock.auth
  
  def test_config(self):
    dummy_cfg = {
      'HOST': 'dummy.serv.er',
      'PORT': 461,
      'BIND_DN': 'cn=oink, ou=grunz',
      'BIND_PASSWORD': 'superS3cr3t',
      'BASE_DN': 'ou=grunz'
    }
    self.app.config['AUTH'] = { 'LDAP': dummy_cfg }
    auth = LDAPUsers()
    self.assertEqual(auth.ldap.host, dummy_cfg.get('HOST'))
    self.assertEqual(auth.ldap.port, dummy_cfg.get('PORT'))
    self.assertEqual(auth.ldap.bind_dn, dummy_cfg.get('BIND_DN'))
    self.assertEqual(auth.ldap.bind_password, dummy_cfg.get('BIND_PASSWORD'))
    self.assertEqual(auth.ldap.base_dn, dummy_cfg.get('BASE_DN'))
    
  def test_sync(self):
    auth = self._setup_mock()
    db_user = auth.sync_user({ 'attributes': { 'cn': 'test.hase', 'mail': 'test@ha.se', 'givenName': 'Test', 'sn': 'Hase' }})
    self.assertEqual(db_user.username, 'test.hase')
    self.assertEqual(db_user.email, 'test@ha.se')
    self.assertEqual(db_user.firstname, 'Test')
    self.assertEqual(db_user.lastname, 'Hase')
    self.assertIsNotNone(db_user.id)
  
  def test_sync_existing(self):
    auth = self._setup_mock()
    user = _create_user()
    user.source = 'ldap'
    db.session.commit()

    db_user = auth.sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname, 'sn': user.lastname }})
    self.assertEqual(db_user.id, user.id)
    self.assertEqual(db_user.firstname, user.firstname)
  
  def test_sync_update(self):
    auth = self._setup_mock()
    user = _create_user()
    user.source = 'ldap'
    db.session.commit()

    db_user = auth.sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname+'oink', 'sn': user.lastname+'oink' }})
    self.assertEqual(db_user.id, user.id)
    self.assertEqual(db_user.firstname, user.firstname)
    self.assertEqual(db_user.lastname, user.lastname)

  def test_sync_inactive(self):
    auth = self._setup_mock()
    user = _create_user()
    user.source = 'ldap'
    user.is_active = False
    db.session.commit()

    with self.assertRaises(UserDisabled):
      db_user = auth.sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname+'oink', 'sn': user.lastname+'oink' }})
    
  def test_sync_local(self):
    auth = self._setup_mock()
    user = _create_user()
    user.source = 'local'
    db.session.commit()

    with self.assertRaises(UserConflict):
      db_user = auth.sync_user({ 'attributes': { 'cn': user.username, 'mail': user.email, 'givenName': user.firstname+'oink', 'sn': user.lastname+'oink' }})



  def test_check(self):
    auth = self._setup_mock()
    user = self.mock.create_user()

    check_user = auth.check_password(user.get('cn'), user.get('userPassword'))
    self.assertEqual(check_user.username, user.get('cn'))

  def test_check_existing(self):
    db_user = _create_user()
    db_user.source = 'ldap'
    db.session.commit()
    auth = self._setup_mock()
    user = self.mock.create_user(name=db_user.username, password='supersecret')

    check_user = auth.check_password(user.get('cn'), user.get('userPassword'))
    self.assertEqual(check_user.id, db_user.id)

  def test_check_twice(self):
    auth = self._setup_mock()
    user = self.mock.create_user()
    other_user = self.mock.create_user(name='oink.hase')

    check_user = auth.check_password(user.get('cn'), user.get('userPassword'))
    check_other_user = auth.check_password(other_user.get('cn'), other_user.get('userPassword'))

  def test_not_found(self):
    auth = self._setup_mock()
    user = self.mock.create_user()

    with self.assertRaises(UserNotFound):
      check_user = auth.check_password('someone', 'somesecret')

  def test_invalid_password(self):
    auth = self._setup_mock()
    user = self.mock.create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('cn'), user.get('userPassword')+'oink')

  def test_invalid_password_recheck(self):
    auth = self._setup_mock()
    user = self.mock.create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('cn'), user.get('userPassword')+'oink')
    
    # should work
    check_user = auth.check_password(user.get('cn'), user.get('userPassword'))
  
  def test_none_password(self):
    auth = self._setup_mock()
    user = self.mock.create_user()

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('cn'), None)

    with self.assertRaises(InvalidPassword):
      check_user = auth.check_password(user.get('cn'), '')

  def test_inactive(self):
    auth = self._setup_mock()
    db_user = _create_user()
    db_user.source = 'ldap'
    db_user.is_active = False

    user = self.mock.create_user(name=db_user.username, password='somesecret')

    with self.assertRaises(UserDisabled):
      check_user = auth.check_password(user.get('cn'), user.get('userPassword'))
  