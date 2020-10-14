from sqlalchemy.orm.exc import NoResultFound
from flask import g

from .exceptions import UserDisabled, UserNotFound, InvalidPassword
from .base import PasswordCheckerBase

class LocalUsers(PasswordCheckerBase):

  def __init__(self):
    pass

  def check_password(self, username, password):
    from Hinkskalle.models import User
    try:
      user = User.query.filter(User.username==username, User.source=='local').one()
    except NoResultFound:
      raise UserNotFound()
      
    if not user.is_active:
      raise UserDisabled()

    if not user.check_password(password):
      raise InvalidPassword()

    g.authenticated_user = user
    return user