from abc import ABC, abstractmethod

class PasswordCheckerBase(ABC):
  @abstractmethod
  def check_password(self, username: str, password: str):
    pass