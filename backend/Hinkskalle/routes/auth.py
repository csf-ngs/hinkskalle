from Hinkskalle import registry, authenticator
from Hinkskalle.util.auth import Scopes
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app

class TokenResponseSchema(ResponseSchema):
  status = fields.String()

@registry.handles(
  rule='/v1/token-status',
  method='GET',
  authenticators=authenticator.with_scope(Scopes.user),
  response_body_schema=TokenResponseSchema(),
)
def token_status():
  return {
    'status': 'welcome'
  }