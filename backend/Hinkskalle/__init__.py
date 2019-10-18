from flask import Flask, send_from_directory, jsonify, json, request, abort
from logging.config import dictConfig

import pprint

app = Flask(__name__)

dictConfig({
  'version': 1,
  'formatters': {
    'standard': {
      'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }
  },
  'handlers': {
    'default': {
      'class': 'logging.StreamHandler',
      'formatter': 'standard',
      'stream': 'ext://sys.stdout',
    }
  },
  'root': {
    'level': 'DEBUG',
    'handlers': ['default'],
  }
})

test_entity = { 'id': 'test-hase', 'name': 'test-hase name', 'description': 'something' }
test_collection = {'id': 'test-coll', 'name': 'test-coll name', 'description': 'something else', 'entity': 'grunz', 'entityName': 'test-hase'}
test_container = { 'id': 'test-oink', 'name': 'oinkoink name', 'imageTags': {'latest': 'eins', 'v1': 'zwei'}, 'collectionName': 'testcoll' }
test_image = { 'id': 'image-test222',
        'hash': 'sha256.50561fafcf34bd08d98e940121abe8eff87061c9a268c75fc68a3aaf79480dc7',
        'entity': 'entity-test',
        'entityName': 'Testhase',
        'collection': 'test',
        'collectionName': 'Teststall',
        'container': 'container-test',
        'containerName': 'grunz',
      }

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/version')
def version():
  return json.dumps({
    'version': '2.0.0',
    'apiVersion': '2.0.0',
  })

@app.route('/assets/config/config.prod.json')
def config():
  return json.dumps({
    'libraryAPI': {
      'uri': 'http://172.28.128.1:7660'
    },
    'keystoreAPI': {
      'uri': 'http://172.28.128.1:7660'
    },
    'tokenAPI': {
      'uri': 'http://172.28.128.1:7660'
    }
  })

@app.route('/v1/token-status')
def token_status():
  # Bearer bla
  app.logger.debug(f"token {request.headers.get('Authorization')}")
  return json.dumps({ 'status': 'welcome!' })

@app.route('/v1/entities/<string:name>')
def get_entity(name):
  return json.dumps({
    'data': test_entity
  })

@app.route('/v1/entities', methods=['POST'])
def create_entity():
  app.logger.debug(request.get_json(force=True))
  return json.dumps({
    'data': test_entity
  })

@app.route('/v1/collections/<string:entity>/<string:collection>')
def get_collection(entity, collection):
  return json.dumps({
    'data': test_collection
  })

@app.route('/v1/collections', methods=['POST'])
def create_collection():
  app.logger.debug(request.get_json(force=True))
  return json.dumps({
    'data': test_collection
  })

@app.route('/v1/containers/<string:entity>/<string:collection>/<string:container>')
def get_container(entity, collection, container):
  return json.dumps({
    'data': test_container
  })

@app.route('/v1/containers', methods=['POST'])
def create_container():
  app.logger.debug(request.get_json(force=True))
  return json.dumps({
    'data': test_container
  })

@app.route('/v1/tags/<string:container>', methods=['GET', 'POST'])
def set_tags(container):
  if request.method == 'POST':
    app.logger.debug(request.get_json(force=True))
  
  return json.dumps({
    'data': { 'latest': 'eins', 'eins': 'zwei' }
  })


@app.route('/v1/search')
def search():
  app.logger.debug(f"token {request.headers.get('Authorization')}")
  app.logger.debug(f"search for {request.args.get('value')}")
  return json.dumps({
    'data': {
      'entity': [ test_entity ],
      'collection': [ test_collection ],
      'container': [ test_container ],
      'image': [],
    }
  })

@app.route('/v1/images/<path:image_ref>')
@app.route('/v1/images//<path:image_ref>')
def get_image(image_ref):
  return json.dumps({ 'data': test_image })

@app.route('/v1/images', methods=['POST'])
def create_image():
  app.logger.debug(request.get_json(force=True))
  return json.dumps({ 'data': test_image })


@app.route('/v1/imagefile/<path:image_ref>', methods=['GET', 'POST'])
@app.route('/v1/imagefile//<path:image_ref>', methods=['GET', 'POST'])
def image_pull(image_ref):
  if request.method == 'GET':
    app.logger.info(image_ref)
    return send_from_directory('../tmp/', 'minimap2.sif')
  elif request.method == 'POST':
    # file comes in as raw body
    read=0
    while (True):
      chunk = request.stream.read(16384)
      if len(chunk) == 0:
        break
      read = read + len(chunk)
    app.logger.debug(f"read {read} bytes")
    return 'Danke!'
