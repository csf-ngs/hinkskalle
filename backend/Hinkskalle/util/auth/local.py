from sqlalchemy.exc import NoResultFound

from .exceptions import UserNotFound, InvalidPassword
from .base import PasswordCheckerBase


class LocalUsers(PasswordCheckerBase):
    def __init__(self):
        pass

    def check_password(self, username: str, password: str):
        from Hinkskalle.models import User

        try:
            user = User.query.filter(User.username == username, User.source == "local").one()
        except NoResultFound:
            raise UserNotFound()

        if not user.check_password(password):
            raise InvalidPassword()

        return user
