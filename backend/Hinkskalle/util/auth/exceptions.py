class UserNotFound(Exception):
  def __init__(self):
    self.message="Username not found"

class UserDisabled(Exception):
  def __init__(self):
    self.message="User is disabled"

class InvalidPassword(Exception):
  def __init__(self):
    self.message="Invalid password"

class UserConflict(Exception):
  def __init__(self):
    self.message="Local user with same username exists"