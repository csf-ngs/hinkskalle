from .base import PasswordCheckerBase
from .exceptions import UserNotFound, InvalidPassword, UserDisabled, UserConflict

from sqlalchemy.orm.exc import NoResultFound 

from ldap3 import Server, Connection, ObjectDef, Reader, SUBTREE, SYNC, SCHEMA
from ldap3.utils.conv import escape_filter_chars
from ldap3.core.exceptions import LDAPBindError, LDAPInvalidCredentialsResult, LDAPPasswordIsMandatoryError

from flask import g, current_app

# mock ldap returns scalar, real ldap (slapd) a list
# make sure we can deal with both
def _get_attr(attr):
  if type(attr) == list:
    return attr[0]
  else:
    return attr

class LDAPService:
  def __init__(self, host=None, port=389, bind_dn=None, bind_password=None, base_dn=None, filter="(cn={})", all_users_filter="(objectClass=Person)", get_info=SCHEMA, client_strategy=SYNC):
    self.host = host
    self.port = int(port) if port else None
    self.bind_dn = bind_dn
    self.bind_password = bind_password
    self.base_dn = base_dn
    self.filter = filter
    self.all_users_filter = all_users_filter

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
  
  def list_users(self):
    self.connection.search(search_base=self.base_dn, search_filter=self.all_users_filter, search_scope=SUBTREE, attributes='*')
    current_app.logger.debug(len(self.connection.response))
    return self.connection.response


class LDAPUsers(PasswordCheckerBase):

  def __init__(self, app=None):
    if app:
      self.app = app
    else:
      self.app = current_app
    self.config = self.app.config.get('AUTH', {}).get('LDAP', {})
    self.app.logger.debug(f"initializing ldap service with host {self.config.get('HOST', '')}")
    self.ldap = LDAPService(host=self.config.get('HOST', ''), port=self.config.get('PORT', 389), bind_dn=self.config.get('BIND_DN'), bind_password=self.config.get('BIND_PASSWORD'), base_dn=self.config.get('BASE_DN'))
  
  def sync_user(self, entry):
    from Hinkskalle import db
    from Hinkskalle.models import User

    attrs = entry.get('attributes')
    try:
      user = User.query.filter(User.username == _get_attr(attrs.get('cn'))).one()

      if not user.is_active:
        raise UserDisabled()

      if not user.source == 'ldap':
        raise UserConflict(username=user.username)

    except NoResultFound:
      user = User()
      user.is_admin = False
      user.is_active = True
    
    user.username = _get_attr(attrs.get('cn'))
    user.email = _get_attr(attrs.get('mail'))
    user.firstname = _get_attr(attrs.get('givenName'))
    user.lastname = _get_attr(attrs.get('sn'))
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

    db_user = self.sync_user(ldap_user)
    g.authenticated_user = db_user
    return db_user
    

