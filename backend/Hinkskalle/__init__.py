from flask import Flask
from flask_session import Session
from flask_rebar import Rebar
from flask_mongoengine import MongoEngineSessionInterface
from logging.config import dictConfig

import os

dictConfig({
  'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d | %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
app.config.from_json(os.environ['HINKSKALLE_SETTINGS'])
app.config['MONGODB_SETTINGS'] = {
  'host': os.environ['MONGODB_HOST']
}

from Hinkskalle.models import db
db.init_app(app)
app.session_interface = MongoEngineSessionInterface(db)

from Hinkskalle.fsk_api import HinkskalleFskApi
from fsk_authenticator import FskAdminAuthenticator, FskAuthenticator
FskAuthenticator.register_fsk_api_class(HinkskalleFskApi)

from Hinkskalle.util.swagger import generator

rebar = Rebar()
registry = rebar.create_handler_registry(prefix="/", swagger_generator=generator)
registry.set_default_authenticator(None)

fsk_auth = FskAuthenticator(key_header='Authorization')
fsk_admin_auth = FskAdminAuthenticator(key_header='Authorization')

import Hinkskalle.routes

# make sure init_app is called after importing routes??
rebar.init_app(app)

if __name__ == '__main__':
    app.run()