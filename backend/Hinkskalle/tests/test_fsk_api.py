import unittest
import os
import os.path
import json

from Hinkskalle.fsk_api import HinkskalleFskApi

def _get_test_data(filename):
  with open(os.path.join(os.path.dirname(__file__), filename), 'r') as fh:
    data = json.load(fh)
  return data


class TestFskApi(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    os.environ['FSK_URL']='https://fa.ke/'
  
  def test_admin(self):
    user = HinkskalleFskApi.sync_scientist(_get_test_data('user_admin.json'))
    self.assertTrue(user.is_admin)
    self.assertEqual(user.username, 'admin.hase')

  def test_user(self):
    user = HinkskalleFskApi.sync_scientist(_get_test_data('user_regular.json'))
    self.assertFalse(user.is_admin)
    self.assertEqual(user.username, 'user.hase')

  def test_drone(self):
    user = HinkskalleFskApi.sync_scientist(_get_test_data('user_drone_puller.json'))
    self.assertTrue(user.is_admin)
    self.assertEqual(user.username, 'drone.puller')

  



