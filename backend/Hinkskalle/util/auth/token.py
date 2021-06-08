from flask.globals import current_app
from flask_rebar.authenticators import Authenticator
from flask import g, request
from flask_rebar import errors
from enum import Enum
import datetime
from base64 import b64decode

_NO_TOKEN='No token found'

class Scopes(Enum):
  optional = 0
  user = 1
  admin = 2

# the pattern with scopes is sort-of stolen from the auth0 authenticator
class ScopedTokenAuthenticator(Authenticator):
  def __init__(self, auth, scope):
    if not isinstance(scope, Scopes):
      raise ValueError('Invalid scope')
    self.authenticator=auth
    self.scope=scope
  
  def authenticate(self):
    try:
      self.authenticator.authenticate()
    except errors.Unauthorized as err:
      if err.error_message == _NO_TOKEN and self.scope == Scopes.optional:
        g.authenticated_user = None
      else:
        raise err
    
    if self.scope == Scopes.admin:
      if not g.authenticated_user.is_admin:
        raise errors.Forbidden('Admin privileges required.')
    
class TokenAuthenticator(Authenticator):
  header = 'Authorization'
  type = 'Bearer'
  name = 'Authorization Header'

  def with_scope(self, scope) -> Authenticator:
    return ScopedTokenAuthenticator(self, scope)
  
  def authenticate(self):
    g.authenticated_user = None
    user = self._get_identity(**self._get_token())

    g.authenticated_user = user

  def _get_identity(self, token:str=None, username:str=None, password:str=None):
    if token:
      return self._get_identity_from_token(token)
    elif username and password:
      return self._get_identity_from_basic(username, password)
    else:
      raise errors.InternalError(f"token/username/password required")
  
  def _get_identity_from_token(self, token:str):
    from Hinkskalle.models import Token
    db_token = Token.query.filter(Token.token == token, Token.deleted == False).first()
    if not db_token:
      current_app.logger.debug(f"Token not found")
      raise errors.Unauthorized('Invalid token')
    if not db_token.user.is_active:
      current_app.logger.debug(f"Account Inactive {db_token.user.username}")
      raise errors.Unauthorized('Account deactivated')
    if db_token.expiresAt and db_token.expiresAt < datetime.datetime.now():
      current_app.logger.debug(f"Token expired {db_token.expiresAt}")
      raise errors.Unauthorized('Token expired')

    if db_token.source == 'auto':
      db_token.refresh()
      from Hinkskalle import db
      db.session.commit()
    return db_token.user
  
  def _get_identity_from_basic(self, username, password):
    from Hinkskalle import password_checkers
    from Hinkskalle.util.auth.exceptions import UserNotFound, UserDisabled, InvalidPassword
    try:
      user = password_checkers.check_password(username, password)
    except (UserNotFound, UserDisabled, InvalidPassword) as err:
      raise errors.Unauthorized(err.message)
    return user

  def _get_token(self):
    auth_header = request.headers.get(self.header)
    if not auth_header:
      current_app.logger.debug(f'{self.header} header not present')
      raise errors.Unauthorized(_NO_TOKEN)

    parts = auth_header.split()
    if len(parts) == 1:
      current_app.logger.debug(f"Token not found in {self.header}/{parts}")
      raise errors.NotAcceptable(f"Token not found in {self.header}")
    elif len(parts) > 2:
      current_app.logger.debug(f"Too many parts in {self.header}/{parts}")
      raise errors.NotAcceptable(f"Too many parts in {self.header}")
    elif parts[0].lower() == 'basic':
      current_app.logger.debug(f"trying basic auth...")
      decoded = b64decode(parts[1]).decode('utf8')
      username, password = decoded.split(':')
      if not username or not password:
        current_app.logger.debug(f"invalid basic auth credentials: {decoded}")
        raise errors.NotAcceptable(f"invalid basic auth credentials")
      return { 'username': username, 'password': password }
    elif parts[0].lower() != self.type.lower():
      current_app.logger.debug(f"Wrong {self.header} header prefix {parts}")
      raise errors.NotAcceptable(f"Wrong {self.header} header prefix {parts[0]}")

    return { 'token': parts[1] }