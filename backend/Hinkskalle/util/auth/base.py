from abc import ABC, abstractmethod
from Hinkskalle.models.User import User

class PasswordCheckerBase(ABC):
  @abstractmethod
  def check_password(self, username: str, password: str) -> User:
    pass