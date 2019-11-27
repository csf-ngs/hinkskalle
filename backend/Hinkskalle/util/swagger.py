from flask_rebar import SwaggerV2Generator
from fsk_authenticator.swagger import register_fsk_authenticator
from Hinkskalle.util.auth import FskOptionalAuthenticator

generator = SwaggerV2Generator()
register_fsk_authenticator(generator)

def convert_authenticator(authenticator):
  return (authenticator.name, {
    'name': authenticator.name,
    'type': 'apiKey',
    'in': 'header',
  })

generator.register_authenticator_converter(
    authenticator_class=FskOptionalAuthenticator,
    converter=convert_authenticator,
)

