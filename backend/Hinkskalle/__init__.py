from flask import Flask
from flask_rebar import Rebar
from logging.config import dictConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

db = SQLAlchemy()
migrate = Migrate()

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
  app.config.from_json(os.environ.get('HINKSKALLE_SETTINGS', '../../conf/config.json'))
  if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI']=os.environ['SQLALCHEMY_DATABASE_URI']

  app.config['PREFERRED_URL_SCHEME']=os.environ.get('PREFERRED_URL_SCHEME', 'http')
  db.init_app(app)
  migrate.init_app(app, db)

  with app.app_context():
    import Hinkskalle.commands
    import Hinkskalle.routes
    # make sure init_app is called after importing routes??
    rebar.init_app(app)

  return app

if __name__ == '__main__':
  app=create_app()
  app.run()
