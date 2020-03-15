from .base import PasswordCheckerBase

class LDAPUsers(PasswordCheckerBase):
  def check_password(self, username, password):
    raise Exception("not implemented yet")