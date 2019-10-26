from Hinkskalle import registry, rebar, fsk_auth
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app, g
import re
from mongoengine.queryset.visitor import Q


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
  value_re = re.compile(args['value'], re.IGNORECASE)
  if g.fsk_user.is_admin:
    query = Q(name=value_re)
  else:
    query = Q(name=value_re) & Q(createdBy=g.fsk_user.username)

  entities = Entity.objects(query)
  collections = Collection.objects(query)
  containers = Container.objects(query)


  return {
    'data': {
      'entity': list(entities),
      'collection': list(collections),
      'container': list(containers),
      #'container': [],
      'image': []
    }
  }
  
