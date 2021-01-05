from Hinkskalle import registry, rebar, authenticator
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema
from marshmallow import fields, Schema
from flask import current_app, g
import re


from Hinkskalle.models import Entity, EntitySchema, Collection, CollectionSchema, Container, ContainerSchema, Image, ImageSchema

class SearchSchema(Schema):
  entity=fields.Nested(EntitySchema, many=True)
  collection=fields.Nested(CollectionSchema, many=True)
  container=fields.Nested(ContainerSchema, many=True)
  image=fields.Nested(ImageSchema, many=True)

class SearchResponseSchema(ResponseSchema):
  data=fields.Nested(SearchSchema)

class SearchQuerySchema(RequestSchema):
  value=fields.String(required=False)
  description=fields.String(required=False)
  arch=fields.String(required=False)
  search=fields.String(required=False)

@registry.handles(
  rule='/v1/search',
  method='GET',
  response_body_schema=SearchResponseSchema(),
  query_string_schema=SearchQuerySchema(),
  authenticators=authenticator.with_scope(Scopes.user),
)
def search():
  args = rebar.validated_args

  search = {
    'entities': [],
    'collections': [],
    'containers': [],
    'images': [],
  }

  if args.get('value', None):
    search['entities'].append(Entity.name.ilike(f"%{args['value']}%"))
    search['collections'].append(Collection.name.ilike(f"%{args['value']}%"))
    search['containers'].append(Container.name.ilike(f"%{args['value']}%"))
    search['images'].append(Image.hash.ilike(f"%.{args['value']}%"))

  if args.get('description', None):
    search['entities'].append(Entity.description.ilike(f"%{args['description']}%"))
    search['collections'].append(Collection.description.ilike(f"%{args['description']}%"))
    search['containers'].append(Container.description.ilike(f"%{args['description']}%"))

  entities = Entity.query.filter(*search['entities'])
  collections = Collection.query.filter(*search['collections'])
  containers = Container.query.filter(*search['containers'])
  images = Image.query.filter(*search['images']).union(Image.query.join(Image.container_ref, aliased=True).filter(*search['containers']))

  return {
    'data': {
      'entity': [ e for e in entities if e.check_access(g.authenticated_user) ],
      'collection': [ c for c in collections if c.check_access(g.authenticated_user) ],
      'container': [ c for c in containers if c.check_access(g.authenticated_user) ],
      #'container': [],
      'image': [ i for i in images if i.check_access(g.authenticated_user) ],
    }
  }
  
