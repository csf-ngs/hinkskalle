from Hinkskalle.models.Container import Container
from sqlalchemy.orm.exc import NoResultFound
from Hinkskalle.models import Image
from flask import current_app, request, make_response, send_file
from flask_rebar import errors
from werkzeug.routing import BaseConverter
import json
from hashlib import sha256

from .util import _get_container as __get_container

def _get_container(name: str) -> Container:
  parts = name.split('/')
  if len(parts) == 1:
    entity='default'
    collection='default'
    container=parts[0]
  elif len(parts) == 2:
    entity='default'
    collection=parts[0]
    container=parts[1]
  elif len(parts) == 3:
    entity = parts[0]
    collection = parts[1]
    container = parts[2]
  else:
    raise errors.NotFound()
  
  return __get_container(entity, collection, container)

# regex from https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pull
class NameConverter(BaseConverter):
  def __init__(self, url_map, *items):
    super(NameConverter, self).__init__(url_map)
    self.regex = '[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*'

current_app.url_map.converters['distname']=NameConverter

# XXX error signalling missing
# error codes: https://github.com/opencontainers/distribution-spec/blob/main/spec.md#error-codes

# pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-manifests
# XXX (temp) store manifest by sha hash 
# oras client fetches first with tag, then re-fetches manifest by sha hash
@current_app.route('/v2/<distname:name>/manifests/<string:reference>')
def oras_manifest(name: str, reference: str):
  # should check accept header for 
  # application/vnd.oci.image.manifest.v1+json
  container = _get_container(name)

  if reference.startswith('sha256:'):
    reference = 'latest'

  image_tags = container.imageTags()
  image = Image.query.get(image_tags[reference]) 

  # see https://github.com/opencontainers/image-spec/blob/master/manifest.md#image-manifest-property-descriptions
  manifest={
      "schemaVersion":2,
      "config":{
        'mediaType': 'application/vnd.sylabs.sif.config.v1',
      },
      "layers":[{ 
          # see https://github.com/opencontainers/image-spec/blob/master/descriptor.md
          'mediaType': 'application/vnd.sylabs.sif.layer.v1.sif',
          'digest': f"sha256:{image.hash.replace('sha256.', '')}",
          'size': image.size,
          # singularity does not pull without a name
          # could provide more annotations!
          'annotations': {
            'org.opencontainers.image.title': container.name,
          }
        },
      ],
    }
  
  # need to provide a checksum for the manifest json
  manifest_json = json.dumps(manifest)
  digest = sha256()
  digest.update(manifest_json.encode('utf8'))
  response = make_response(manifest_json)
  response.headers['Content-Type']='application/vnd.oci.image.manifest.v1+json'
  response.headers['Docker-Content-Digest']=f'sha256:{digest.hexdigest()}'
  return response
  

# blob pull spec https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pulling-blobs
# we can only support sha256 (would need to pre-calculate more hashes)
@current_app.route('/v2/<distname:name>/blobs/<string:digest>')
def oras_blob(name, digest):
  # check accept header for
  # application/vnd.sylabs.sif.layer.v1.sif
  if not digest.startswith('sha256:'):
    raise errors.InternalError()
  
  container = _get_container(name)
  try:
    image = container.images_ref.filter(Image.hash == f"sha256.{digest.replace('sha256:', '')}").one()
  except NoResultFound:
    raise errors.NotFound()
  
  return send_file(image.location) 
