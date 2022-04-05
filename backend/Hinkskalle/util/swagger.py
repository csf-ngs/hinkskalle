from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.authenticator_to_swagger import AuthenticatorConverterRegistry
from flask_rebar.swagger_generation.authenticator_to_swagger import make_class_from_method
from flask_rebar.swagger_generation.marshmallow_to_swagger import NestedConverter, request_body_converter_registry, response_converter_registry

from .auth.token import TokenAuthenticator, ScopedTokenAuthenticator

def register_authenticators(registry: AuthenticatorConverterRegistry):
  registry.register_type(auth_converter)
  registry.register_type(scoped_auth_converter)

def _convert_authenticator(authenticator):
  definition = { sw.name: authenticator.type, sw.in_: authenticator.header, sw.type_: sw.api_key }
  return 'token_auth', definition

def _convert_scoped_authenticator(authenticator):
  return _convert_authenticator(authenticator.authenticator)

auth_converter = make_class_from_method(TokenAuthenticator, _convert_authenticator)
scoped_auth_converter = make_class_from_method(ScopedTokenAuthenticator, _convert_scoped_authenticator)

# see https://github.com/plangrid/flask-rebar/issues/90
class MyNestedConverter(NestedConverter):
    def convert(self, obj, context):
        inst = obj.schema # <-- here is the fix
        if obj.many:
            return {sw.type_: sw.array, sw.items: context.convert(inst, context)}
        else:
            return context.convert(inst, context)

request_body_converter_registry.register_type(MyNestedConverter())
response_converter_registry.register_type(MyNestedConverter())