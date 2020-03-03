from Hinkskalle import registry, rebar, fsk_auth, fsk_admin_auth, db
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema
from flask import request, current_app, g
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import datetime

from Hinkskalle.models import CollectionSchema, Collection, Entity

from fsk_authenticator import FskAdminAuthenticator

class CollectionResponseSchema(ResponseSchema):
  data = fields.Nested(CollectionSchema)

class CollectionListResponseSchema(ResponseSchema):
  data = fields.Nested(CollectionSchema, many=True)

class CollectionCreateSchema(CollectionSchema, RequestSchema):
  pass

class CollectionUpdateSchema(CollectionSchema, RequestSchema):
  name = fields.String(dump_only=True)
  entity = fields.String(dump_only=True)

def _get_collection(entity_id, collection_id):
  try:
    entity = db.session.query(Entity).filter(Entity.name==entity_id).one()
  except NoResultFound:
    raise errors.NotFound(f"entity {entity_id} not found")
  try:
    collection = entity.collections_ref.filter(Collection.name==collection_id).one()
  except NoResultFound:
    raise errors.NotFound(f"collection {entity.id}/{collection_id} not found")
  return collection

@registry.handles(
  rule='/v1/collections/<string:entity_id>',
  method='GET',
  response_body_schema=CollectionListResponseSchema(),
  authenticators=fsk_auth,
)
def list_collections(entity_id):
  try:
    entity = db.session.query(Entity).filter(Entity.name==entity_id).one()
  except NoResultFound:
    raise errors.NotFound(f"entity {entity_id} not found")
  if not entity.check_access(g.fsk_user):
    raise errors.Forbidden(f"access denied.")

  if g.fsk_user.is_admin:
    objs = db.session.query(Collection).filter(Collection.entity_id == entity.id).all()
  else:
    objs = db.session.query(Collection).filter(Collection.entity_id == entity.id, Collection.createdBy==g.fsk_user.username).all()
  
  return { 'data': list(objs) }

@registry.handles(
  rule='/v1/collections/<string:entity_id>/<string:collection_id>',
  method='GET',
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_auth,
)
def get_collection(entity_id, collection_id):
  collection = _get_collection(entity_id, collection_id)
  if not collection.check_access(g.fsk_user):
    raise errors.Forbidden(f"access denied.")
  return { 'data': collection }

@registry.handles(
  rule='/v1/collections/<string:entity_id>/',
  method='GET',
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_auth
)
def get_default_collection(entity_id):
  current_app.logger.debug('get default collection')
  return get_collection(entity_id=entity_id, collection_id='default')

@registry.handles(
  rule='/v1/collections/',
  method='GET',
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_auth
)
def get_default_collection_default_entity():
  return get_collection(entity_id='default', collection_id='default')


@registry.handles(
  rule='/v1/collections',
  method='POST',
  request_body_schema=CollectionCreateSchema(),
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_auth,
)
def create_collection():
  body = rebar.validated_body
  entity = Entity.query.get(body['entity'])
  if not entity.check_update_access(g.fsk_user):
    raise errors.Forbidden("access denied")
  body.pop('entity')
  if not body['name']:
    body['name']='default'
  
  if entity.name == 'default' and not g.fsk_user.is_admin:
    if body['name'] == 'default' or body['name'] == 'pipeline':
      raise errors.Forbidden("Trying to use a reserved name in the default namespace.")
  new_collection = Collection(**body)
  new_collection.entity_ref=entity
  if entity.defaultPrivate:
    new_collection.private=True
  new_collection.createdBy=g.fsk_user.username

  try:
    db.session.add(new_collection)
    db.session.commit()
  except IntegrityError as err:
    current_app.logger.debug(err)
    raise errors.PreconditionFailed(f"Collection {new_collection.id} already exists")

  return { 'data': new_collection }

@registry.handles(
  rule='/v1/collections/<string:entity_id>/<string:collection_id>',
  method='PUT',
  request_body_schema=CollectionUpdateSchema(),
  response_body_schema=CollectionResponseSchema(),
  authenticators=fsk_auth,
)
def update_collection(entity_id, collection_id):
  body = rebar.validated_body
  collection = _get_collection(entity_id, collection_id)
  if not collection.check_update_access(g.fsk_user):
    raise errors.Forbidden("Access denied to collection")
  
  for key in body:
    setattr(collection, key, body[key])
  collection.updatedAt = datetime.datetime.now()
  db.session.commit()

  return { 'data': collection }