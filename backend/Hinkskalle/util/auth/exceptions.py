class HinkException(Exception):
  def __init__(self):
    self.message = "Major unknown unexpected surprising Hinkskalle fail"

  def __str__(self):
    return self.message

class UserNotFound(HinkException):
  def __init__(self):
    self.message="Username not found"

class UserDisabled(HinkException):
  def __init__(self):
    self.message="User is disabled"

class PasswordAuthDisabled(HinkException):
  def __init__(self):
    self.message="Password authentication is disabled"

class InvalidPassword(HinkException):
  def __init__(self):
    self.message="Invalid password"

class UserConflict(HinkException):
  def __init__(self, username=''):
    self.message=f"Local user with same username {username} exists"