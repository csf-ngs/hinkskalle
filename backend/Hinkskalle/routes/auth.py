from Hinkskalle import registry, fsk_auth
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app

class TokenResponseSchema(ResponseSchema):
  status = fields.String()

@registry.handles(
  rule='/v1/token-status',
  method='GET',
  authenticators=fsk_auth,
  response_body_schema=TokenResponseSchema(),
)
def token_status():
  return {
    'status': 'welcome'
  }