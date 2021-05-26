from flask import current_app
from flask_rebar import errors
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from Hinkskalle.models import Entity, Collection, Container

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
    raise errors.NotFound(f"container {collecion.entityName()}/{collection.name}/{container_id} not found")
  return container
