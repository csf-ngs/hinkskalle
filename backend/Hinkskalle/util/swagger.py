from flask_rebar import HandlerRegistry
from flask_rebar.swagger_generation import swagger_words as sw

from .auth import TokenAuthenticator, ScopedTokenAuthenticator

# this has very much been stolen from the auth0 authenticator

def register_authenticators(registry: HandlerRegistry):
  registry.swagger_generator.register_authenticator_converter(TokenAuthenticator, _convert_authenticator)
  registry.swagger_generator.register_authenticator_converter(ScopedTokenAuthenticator, _convert_scoped_authenticator)

def _convert_authenticator(authenticator):
  definition = { sw.name: authenticator.type, sw.in_: authenticator.header, sw.type_: sw.api_key }
  return 'token_auth', definition

def _convert_scoped_authenticator(authenticator):
  return _convert_authenticator(authenticator.authenticator)
