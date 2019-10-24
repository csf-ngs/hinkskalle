from flask import current_app
import os

from forskalle_api import FskApi

class FskUser():
  def __init__(self, username, is_admin):
    self.username=username
    self.is_admin=True if username=='drone.puller' else bool(is_admin)

class HinkskalleFskApi(FskApi):
  def __init__(self, base=os.environ.get('FSK_URL'), **kwargs):
    super().__init__(base, **kwargs)

  @staticmethod
  def sync_scientist(fsk_user_json):
    return FskUser(fsk_user_json['username'], fsk_user_json.get('is_admin', False))