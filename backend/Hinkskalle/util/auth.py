from fsk_authenticator import FskAuthenticator
from flask import g

class FskOptionalAuthenticator(FskAuthenticator):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.name = 'Fsk Optional'

  def authenticate(self):
    try:
      super().authenticate()
    except:
      g.fsk_api = None
      g.fsk_user = None
