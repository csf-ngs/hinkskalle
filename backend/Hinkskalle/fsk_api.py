from flask import current_app

from forskalle_api import FskApi

class FskUser():
  def __init__(self, username, is_admin):
    self.username=username
    self.is_admin=is_admin

class HinkskalleFskApi(FskApi):
  @staticmethod
  def sync_scientist(fsk_user_json):
    is_admin = any([ group['name']=="Admin" for group in fsk_user_json['groups'] ])
    return FskUser(fsk_user_json['username'], is_admin)