from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    AuthenticatorConverterRegistry,
    AuthenticatorConverter,
)

# from flask_rebar.swagger_generation.authenticator_to_swagger import make_class_from_method

from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    NestedConverter,
    request_body_converter_registry,
    response_converter_registry,
)

from .auth.token import TokenAuthenticator, ScopedTokenAuthenticator


class TokenAuthConverter(AuthenticatorConverter):
    AUTHENTICATOR_TYPE = TokenAuthenticator

    def get_security_schemes(self, obj, context=None):
        return {obj.name: {sw.type_: sw.api_key, sw.in_: TokenAuthenticator.header, sw.name: TokenAuthenticator.type}}

    def get_security_requirements(self, obj, context=None):
        return [{obj.name: []}]


class ScopedTokenAuthConverter(AuthenticatorConverter):
    AUTHENTICATOR_TYPE = ScopedTokenAuthenticator

    def get_security_schemes(self, obj, context=None):
        return {
            "token_auth": {sw.type_: sw.api_key, sw.in_: TokenAuthenticator.header, sw.name: TokenAuthenticator.type}
        }

    def get_security_requirements(self, obj, context=None):
        return [{"token_auth": []}]


def register_authenticators(registry: AuthenticatorConverterRegistry):
    registry.register_type(TokenAuthConverter())
    registry.register_type(ScopedTokenAuthConverter())


# see https://github.com/plangrid/flask-rebar/issues/90
class MyNestedConverter(NestedConverter):
    def convert(self, obj, context):
        inst = obj.schema  # <-- here is the fix
        if obj.many:
            return {sw.type_: sw.array, sw.items: context.convert(inst, context)}
        else:
            return context.convert(inst, context)


request_body_converter_registry.register_type(MyNestedConverter())
response_converter_registry.register_type(MyNestedConverter())
