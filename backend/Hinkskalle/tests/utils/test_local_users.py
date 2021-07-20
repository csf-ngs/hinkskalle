from Hinkskalle import db
from ..model_base import ModelBase
from .._util import _create_user

from Hinkskalle.util.auth.local import LocalUsers
from Hinkskalle.util.auth.exceptions import *

class TestLocalUsers(ModelBase):
  def test_check(self):
    user = _create_user()
    user.source = 'local'
    user.set_password('supersecret')
    db.session.commit()

    check_user = LocalUsers().check_password(user.username, 'supersecret')
    self.assertEqual(user, check_user)
  
  def test_not_found(self):
    with self.assertRaises(UserNotFound):
      check_user = LocalUsers().check_password('someone', 'somesecret')
  
  def test_disabled(self):
    user = _create_user()
    user.source = 'local'
    user.is_active = False
    db.session.commit()

    with self.assertRaises(UserDisabled):
      check_user = LocalUsers().check_password(user.username, 'somesecret')
    
  def test_invalid_password(self):
    user = _create_user()
    user.source = 'local'
    user.set_password('supersecret')
    db.session.commit()

    with self.assertRaises(InvalidPassword):
      check_user = LocalUsers().check_password(user.username, 'fail')
  
  def test_none_password(self):
    user = _create_user()
    user.source = 'local'
    db.session.commit()

    with self.assertRaises(InvalidPassword):
      check_user = LocalUsers().check_password(user.username, 'fail')

  def test_password_not_supplied(self):
    user = _create_user()
    user.source = 'local'
    db.session.commit()

    with self.assertRaises(InvalidPassword):
      check_user = LocalUsers().check_password(user.username, None)

    user.set_password('supersecret')
    db.session.commit()

    with self.assertRaises(InvalidPassword):
      check_user = LocalUsers().check_password(user.username, None)

  def test_not_local(self):
    user = _create_user()
    user.source = 'mars'
    user.set_password('supersecret')
    db.session.commit()

    with self.assertRaises(UserNotFound):
      check_user = LocalUsers().check_password(user.username, 'supersecret')