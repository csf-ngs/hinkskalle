from Hinkskalle import registry, rebar, fsk_auth
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app, g
import re


from Hinkskalle.models import Entity, EntitySchema, Collection, CollectionSchema, Container, ContainerSchema, ImageSchema

class SearchSchema(Schema):
  entity=fields.Nested(EntitySchema, many=True)
  collection=fields.Nested(CollectionSchema, many=True)
  container=fields.Nested(ContainerSchema, many=True)
  image=fields.Nested(ImageSchema, many=True)

class SearchResponseSchema(ResponseSchema):
  data=fields.Nested(SearchSchema)

class SearchQuerySchema(RequestSchema):
  value=fields.String()

@registry.handles(
  rule='/v1/search',
  method='GET',
  response_body_schema=SearchResponseSchema(),
  query_string_schema=SearchQuerySchema(),
  authenticators=fsk_auth,
)
def search():
  args = rebar.validated_args

  entities = Entity.query.filter(Entity.name.ilike(f"%{args['value']}%"))
  collections = Collection.query.filter(Collection.name.ilike(f"%{args['value']}%"))
  containers = Container.query.filter(Container.name.ilike(f"%{args['value']}%"))

  if not g.fsk_user.is_admin:
    entities = entities.filter(Entity.createdBy==g.fsk_user.username)
    collections = collections.filter(Collection.createdBy==g.fsk_user.username)
    containers = containers.filter(Container.createdBy==g.fsk_user.username)

  return {
    'data': {
      'entity': list(entities),
      'collection': list(collections),
      'container': list(containers),
      #'container': [],
      'image': []
    }
  }
  
