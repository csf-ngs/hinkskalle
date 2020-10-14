from .base import PasswordCheckerBase
from .exceptions import UserNotFound, InvalidPassword, UserDisabled, UserConflict

from sqlalchemy.orm.exc import NoResultFound 

from ldap3 import Server, Connection, ObjectDef, Reader, SUBTREE, SYNC, SCHEMA
from ldap3.utils.conv import escape_filter_chars
from ldap3.core.exceptions import LDAPBindError, LDAPInvalidCredentialsResult, LDAPPasswordIsMandatoryError

from flask import g, current_app

class LDAPService:
  def __init__(self, host=None, port=389, bind_dn=None, bind_password=None, base_dn=None, filter="(cn={})", get_info=SCHEMA, client_strategy=SYNC):
    self.host = host
    self.port = port
    self.bind_dn = bind_dn
    self.bind_password = bind_password
    self.base_dn = base_dn
    self.filter = filter

    self.server = Server(host=self.host, port=self.port, get_info=get_info)
    self.connection = Connection(self.server, self.bind_dn, self.bind_password, raise_exceptions=True, client_strategy=client_strategy)
  
  def connect(self):
    self.connection.rebind(user=self.bind_dn, password=self.bind_password)
  
  def close(self):
    self.connection.unbind()
  
  def search_user(self, username):
    self.connection.search(search_base=self.base_dn, search_filter=self.filter.format(escape_filter_chars(username)), search_scope=SUBTREE, attributes='*')
    if len(self.connection.response) == 0:
      raise UserNotFound()
    return self.connection.response[0]
  



class LDAPUsers(PasswordCheckerBase):

  def __init__(self):
    self.config = current_app.config.get('AUTH', {}).get('LDAP', {})
    self.ldap = LDAPService(host=self.config.get('HOST', ''), port=self.config.get('PORT', 389), bind_dn=self.config.get('BIND_DN'), bind_password=self.config.get('BIND_PASSWORD'), base_dn=self.config.get('BASE_DN'))
  
  def _sync_user(self, entry):
    from Hinkskalle import db
    from Hinkskalle.models import User

    attrs = entry.get('attributes')
    try:
      user = User.query.filter(User.username==attrs.get('cn')).one()

      if not user.is_active:
        raise UserDisabled()

      if not user.source == 'ldap':
        raise UserConflict()

    except NoResultFound:
      user = User()
    
    user.username = attrs.get('cn')
    user.email = attrs.get('mail')
    user.firstname = attrs.get('givenName')
    user.lastname = attrs.get('sn')
    user.is_admin = False
    user.is_active = True
    user.source = 'ldap'

    db.session.add(user)
    db.session.commit()
    return user

  def check_password(self, username, password):
    self.ldap.connect()
    ldap_user = self.ldap.search_user(username)
    try:
      self.ldap.connection.rebind(user=ldap_user.get('dn'), password=password)
    except (LDAPInvalidCredentialsResult, LDAPPasswordIsMandatoryError):
      raise InvalidPassword()
    self.ldap.close()

    db_user = self._sync_user(ldap_user)
    g.authenticated_user = db_user
    return db_user
    


