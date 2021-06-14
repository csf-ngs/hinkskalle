from Hinkskalle import registry, authenticator

from Hinkskalle.util.auth.token import Scopes

from flask import g
from flask_rebar import ResponseSchema, errors
from marshmallow import fields
from Hinkskalle.models.Manifest import Manifest, ManifestSchema

from .util import _get_container

class ManifestListResponseSchema(ResponseSchema):
  data = fields.Nested(ManifestSchema, many=True)

@registry.handles(
  rule='/v1/containers/<string:entity_id>/<string:collection_id>/<string:container_id>/manifests',
  method='GET',
  response_body_schema=ManifestListResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user)
)
def list_manifests(entity_id, collection_id, container_id):
  container = _get_container(entity_id, collection_id, container_id)
  if not container.check_access(g.authenticated_user):
    raise errors.Forbidden('access denied')
  
  return { 'data': list(container.manifests_ref) }