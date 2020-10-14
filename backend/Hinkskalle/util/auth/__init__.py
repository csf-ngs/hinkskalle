from .local import LocalUsers
from .ldap import LDAPUsers
from .exceptions import UserNotFound

class PasswordAuthenticators():
  def __init__(self, app=None):
    self.config={}
    self.checkers=[]
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    self.config = app.config.get('AUTH', {})
    self.checkers=[]
    if self.config.get('LDAP'):
      self.checkers.append(LDAPUsers())
    self.checkers.append(LocalUsers())
  
  def check_password(self, username, password):
    for checker in self.checkers:
      try:
        user = checker.check_password(username, password)
        if user:
          return user
      except UserNotFound:
        pass
    raise UserNotFound()
