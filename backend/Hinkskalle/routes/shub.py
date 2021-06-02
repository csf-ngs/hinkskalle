from Hinkskalle import registry, db
from flask_rebar import ResponseSchema, errors
from marshmallow import fields, Schema
from sqlalchemy.orm.exc import NoResultFound
from flask import url_for, current_app

from Hinkskalle.models import Entity, Collection, Container, Image
from Hinkskalle.routes.images import _parse_tag

from .util import _get_container

class ManifestResponseSchema(ResponseSchema):
  image = fields.String(required=True)
  name = fields.String(required=True)
  tag = fields.String(required=True)
  version = fields.String(allow_none=True)
  commit = fields.String(allow_none=True)

@registry.handles(
  rule='/api/container/<string:collection_id>/<string:tagged_container_id>',
  method='GET',
  response_body_schema=ManifestResponseSchema(),
)
def get_manifest(collection_id, tagged_container_id):
  container_id, tag = _parse_tag(tagged_container_id)
  container = _get_container('default', collection_id, container_id)

  if container.private or container.collection_ref.private:
    raise errors.Forbidden(f"container {container_id} is private.")
  
  image_tags = container.imageTags()
  if not tag in image_tags:
    raise errors.NotFound(f"Tag {tag} on container {container.collectionName()}/{container.name} does not exist.")

  return {
    'image': url_for('pull_image', entity_id='default', collection_id=container.collectionName(), tagged_container_id=f"{container.name}:{tag}", _external=True),
    'name': container.name,
    'tag': tag,
  }


