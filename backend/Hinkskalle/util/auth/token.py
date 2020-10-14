from flask_rebar.authenticators import Authenticator
from flask import g, request
from flask_rebar import errors
from enum import Enum

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
    token = self._get_token()
    user = self._get_identity(token)

    g.authenticated_user = user

  def _get_identity(self, token):
    from Hinkskalle.models import Token
    db_token = Token.query.filter(Token.token == token).first()
    if not db_token:
      raise errors.Unauthorized('Invalid token')
    if not db_token.user.is_active:
      raise errors.Unauthorized('Account deactivated')
    return db_token.user

  def _get_token(self):
    auth_header = request.headers.get(self.header)
    if not auth_header:
      raise errors.Unauthorized(_NO_TOKEN)

    parts = auth_header.split()
    if parts[0].lower() != self.type.lower():
      raise errors.NotAcceptable(f"Wrong {self.header} header prefix {parts[0]}")
    elif len(parts) == 1:
      raise errors.NotAcceptable(f"Token not found in {self.header}")
    elif len(parts) > 2:
      raise errors.NotAcceptable(f"Too many parts in {self.header}")

    return parts[1]