from Hinkskalle import registry, rebar
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app
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
)
def search():
  args = rebar.validated_args
  value_re = re.compile(args['value'], re.IGNORECASE)
  #entities = Entity.objects.filter(Q(id__match=args['value']) | Q(name__match=args['value']))
  entities = Entity.objects.filter(name=value_re)
  collections = Collection.objects.filter(name=value_re)
  containers = Container.objects.filter(name=value_re)

  return {
    'data': {
      'entity': list(entities),
      'collection': list(collections),
      'container': list(containers),
      #'container': [],
      'image': []
    }
  }
  
