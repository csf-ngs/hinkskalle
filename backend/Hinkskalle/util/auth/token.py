from flask import current_app
from flask_rebar.authenticators import Authenticator
from flask import g, request
from flask_rebar import errors
from enum import Enum
import datetime

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

  def with_scope(self, scope) -> ScopedTokenAuthenticator:
    return ScopedTokenAuthenticator(self, scope)
  
  def authenticate(self):
    g.authenticated_user = None
    token = self._get_identity(self._get_token())
    if token.source == 'auto':
      token.refresh()
      from Hinkskalle import db
      db.session.commit()

    g.authenticated_user = token.user

  def _get_identity(self, token):
    from Hinkskalle.models import Token
    db_token = Token.query.filter(Token.token == token, Token.deleted == False).first()
    if not db_token:
      current_app.logger.debug('Token not in db')
      raise errors.Unauthorized('Invalid token')
    if not db_token.user.is_active:
      current_app.logger.debug(f'{db_token.user.username} deactivated')
      raise errors.Unauthorized('Account deactivated')
    if db_token.expiresAt and db_token.expiresAt < datetime.datetime.now():
      current_app.logger.debug(f'token expired at {db_token.expiresAt}')
      raise errors.Unauthorized('Token expired')
    return db_token

  def _get_token(self):
    auth_header = request.headers.get(self.header)
    if not auth_header:
      current_app.logger.debug(f"No {self.header} header")
      raise errors.Unauthorized(_NO_TOKEN)

    parts = auth_header.split()
    if parts[0].lower() == 'basic':
      current_app.logger.debug('passing on basic auth')
      raise errors.Unauthorized(_NO_TOKEN)
    if parts[0].lower() != self.type.lower():
      current_app.logger.debug(f"Wrong {self.header} header prefix {parts[0]}")
      raise errors.NotAcceptable(f"Wrong {self.header} header prefix {parts[0]}")
    elif len(parts) == 1:
      current_app.logger.debug(f"Token not found in {self.header}/{parts}")
      raise errors.NotAcceptable(f"Token not found in {self.header}")
    elif len(parts) > 2:
      current_app.logger.debug(f"Too many parts in {self.header}/{parts}")
      raise errors.NotAcceptable(f"Too many parts in {self.header}")

    return parts[1]