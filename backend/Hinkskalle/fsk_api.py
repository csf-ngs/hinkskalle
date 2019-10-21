from flask import current_app

from forskalle_api import FskApi

class FskUser():
  def __init__(self, username, is_admin):
    self.username=username
    self.is_admin=is_admin

class HinkskalleFskApi(FskApi):
  @staticmethod
  def sync_scientist(fsk_user_json):
    return FskUser(fsk_user_json['username'], fsk_user_json.get('is_admin', False))