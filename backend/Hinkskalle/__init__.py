from flask import Flask
from flask_rebar import Rebar
from logging.config import dictConfig

import os

rebar = Rebar()
from Hinkskalle.util.swagger import generator

registry = rebar.create_handler_registry(prefix="/", swagger_generator=generator)
registry.set_default_authenticator(None)

from Hinkskalle.fsk_api import HinkskalleFskApi
from fsk_authenticator import FskAdminAuthenticator, FskAuthenticator
from Hinkskalle.util.auth import FskOptionalAuthenticator

FskAuthenticator.register_fsk_api_class(HinkskalleFskApi)
fsk_auth = FskAuthenticator(key_header='Authorization')
fsk_admin_auth = FskAdminAuthenticator(key_header='Authorization')
fsk_optional_auth = FskOptionalAuthenticator(key_header='Authorization')


def create_app():
  dictConfig({
    'version': 1,
      'formatters': {
        'default': {
          'format': '[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d | %(message)s',
        },
        'access': {
          'format': '%(message)s',
        },
      },
      'handlers': {
        'wsgi': {
          'class': 'logging.StreamHandler',
          'stream': 'ext://flask.logging.wsgi_errors_stream',
          'formatter': 'default'
        },
        'wsgi_access': {
          'class': 'logging.StreamHandler',
          'stream': 'ext://flask.logging.wsgi_errors_stream',
          'formatter': 'access'
        },
      },
      'root': {
          'level': 'DEBUG',
          'handlers': ['wsgi']
      },
      'loggers': {
        'gunicorn.access': {
          'level': 'INFO',
          'handlers': ['wsgi_access'],
          'propagate': False,
        }
      }
  })

  app = Flask(__name__)
  app.config.from_json(os.environ['HINKSKALLE_SETTINGS'])
  if 'MONGODB_HOST' in os.environ:
    app.config['MONGODB_SETTINGS'] = {
      'host': os.environ['MONGODB_HOST'],
      'username': os.environ.get('MONGODB_USERNAME', None),
      'password': os.environ.get('MONGODB_PASSWORD', None),
    }
  app.config['PREFERRED_URL_SCHEME']=os.environ.get('PREFERRED_URL_SCHEME', 'http')
  from Hinkskalle.models import db
  db.init_app(app)

  with app.app_context():
    import Hinkskalle.routes
    # make sure init_app is called after importing routes??
    rebar.init_app(app)

  return app

if __name__ == '__main__':
  app=create_app()
  app.run()
