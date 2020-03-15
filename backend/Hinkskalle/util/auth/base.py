from abc import ABC, abstractmethod

class PasswordCheckerBase(ABC):
  @abstractmethod
  def check_password(self, username, password):
    pass