from flask import current_app, request
from flask_rebar import errors
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from flask_rebar import RequestSchema
from marshmallow import fields

from Hinkskalle.models import Entity, Collection, Container

class DownloadQuerySchema(RequestSchema):
  temp_token = fields.String(required=False)

def _get_service_url():
  service_url = request.url_root.rstrip('/')
  if current_app.config.get('PREFERRED_URL_SCHEME', 'http') == 'https':
    service_url = service_url.replace('http:', 'https:')
  return service_url

def _get_entity(entity_id: str) -> Entity:
  try:
    entity = Entity.query.filter(func.lower(Entity.name)==entity_id.lower()).one()
  except NoResultFound:
    current_app.logger.debug(f"entity {entity_id} not found")
    raise errors.NotFound(f"entity {entity_id} not found")
  return entity

def _get_collection(entity_id: str, collection_id: str) -> Collection:
  entity = _get_entity(entity_id)
  try:
    collection = entity.collections_ref.filter(func.lower(Collection.name)==collection_id.lower()).one()
  except NoResultFound:
    current_app.logger.debug(f"collection {entity.name}/{collection_id} not found")
    raise errors.NotFound(f"collection {entity.name}/{collection_id} not found")
  return collection


def _get_container(entity_id: str, collection_id: str, container_id: str) -> Container:
  collection = _get_collection(entity_id, collection_id)
  try:
    container = collection.containers_ref.filter(func.lower(Container.name)==container_id.lower()).one()
  except NoResultFound:
    current_app.logger.debug(f"container {collection.entityName()}/{collection.name}/{container_id} not found")
    raise errors.NotFound(f"container {collection.entityName()}/{collection.name}/{container_id} not found")
  return container
