import json
from flask import Flask
from flask_rebar import Rebar, SwaggerV2Generator
from flask_rebar.swagger_generation.authenticator_to_swagger import AuthenticatorConverterRegistry

from logging.config import dictConfig
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate

import os
import os.path

from werkzeug.routing import BaseConverter

auth_registry = AuthenticatorConverterRegistry()
from Hinkskalle.util.swagger import register_authenticators
register_authenticators(auth_registry)

generator = SwaggerV2Generator(authenticator_converter_registry=auth_registry)



rebar = Rebar()
registry = rebar.create_handler_registry(swagger_generator=generator, prefix='/')
registry.set_default_authenticator(None)

from Hinkskalle.util.auth.token import TokenAuthenticator
authenticator = TokenAuthenticator()
from Hinkskalle.util.auth import PasswordAuthenticators
password_checkers = PasswordAuthenticators()


# see https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()

# regex from https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pull
class OrasNameConverter(BaseConverter):
  regex = '[a-zA-Z0-9]+([._-][a-zA-Z0-9]+)*(/[a-zA-Z0-9]+([._-][a-zA-Z0-9]+)*)*'
  part_isolating = False


def create_app():
  app = Flask(__name__)
  app.config.from_file(os.environ.get('HINKSKALLE_SETTINGS', '../../conf/config.json'), load=json.load)
  secrets_conf = os.environ.get('HINKSKALLE_SECRETS', '../../conf/secrets.json')
  if os.path.exists(secrets_conf):
    app.config.from_file(secrets_conf, load=json.load)

  if not app.config.get('DEFAULT_ARCH'):
    app.config['DEFAULT_ARCH']='amd64'
  if 'HINKSKALLE_SECRET_KEY' in os.environ:
    app.config['SECRET_KEY'] = os.getenv('HINKSKALLE_SECRET_KEY')
  if app.config.get('SECRET_KEY') is None:
    raise Exception('please configure SECRET_KEY in config.json or HINKSKALLE_SECRET_KEY as environment variable')
  if 'DB_PASSWORD' in os.environ:
    app.config['DB_PASSWORD'] = os.getenv('DB_PASSWORD')
  if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

  if app.config.get('DB_PASSWORD'):
    app.config['SQLALCHEMY_DATABASE_URI']=app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('%PASSWORD%', app.config.get('DB_PASSWORD'))
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS', False)

  if not 'AUTH' in app.config:
    app.config['AUTH']={}

  app.config['PREFERRED_URL_SCHEME'] = app.config.get('PREFERRED_URL_SCHEME', 'http')
  if 'PREFERRED_URL_SCHEME' in os.environ:
    app.config['PREFERRED_URL_SCHEME']=os.getenv('PREFERRED_URL_SCHEME')

  app.config['KEYSERVER_URL'] = app.config.get('KEYSERVER_URL', 'https://sks.hnet.se')
  if 'HINKSKALLE_KEYSERVER_URL' in os.environ:
    app.config['KEYSERVER_URL']=os.environ.get('HINKSKALLE_KEYSERVER_URL')

  if 'RQ_CONNECTION_CLASS' in os.environ:
    app.config['RQ_CONNECTION_CLASS'] = os.environ.get('RQ_CONNECTION_CLASS')
  if 'RQ_ASYNC' in os.environ:
    app.config['RQ_ASYNC']=os.environ.get('RQ_ASYNC')=='1'

  app.config['IMAGE_PATH_HASH_LEVEL'] = app.config.get('IMAGE_PATH_HASH_LEVEL', 2)
  app.config['MULTIPART_UPLOAD_CHUNK'] = app.config.get('MULTIPART_UPLOAD_CHUNK', 64*1024*1024)
  app.config['FRONTEND_PATH'] = app.config.get('FRONTEND_PATH', os.path.abspath('../frontend/dist'))

  ldap_conf = app.config['AUTH'].get('LDAP', {})
  for key in ['ENABLED', 'HOST', 'PORT', 'BIND_DN', 'BIND_PASSWORD', 'BASE_DN']:
    if 'HINKSKALLE_LDAP_' + key in os.environ:
      ldap_conf[key]=os.environ.get('HINKSKALLE_LDAP_'+key)
      if key == 'ENABLED':
        ldap_conf[key]=ldap_conf[key] != "0" and ldap_conf[key] != ""
  if len(ldap_conf) > 0:
    app.config['AUTH']['LDAP'] = app.config['AUTH'].get('LDAP', {})
    for k, v in ldap_conf.items():
      app.config['AUTH']['LDAP'][k]=v
  
  app.config['DOWNLOAD_TOKEN_EXPIRATION'] = app.config.get('DOWNLOAD_TOKEN_EXPIRATION', 86400)

  app.config['BACKEND_URL'] = os.environ.get('HINKSKALLE_BACKEND_URL', app.config.get('BACKEND_URL', None))
  app.config['FRONTEND_URL'] = os.environ.get('HINKSKALLE_FRONTEND_URL', app.config.get('FRONTEND_URL', app.config['BACKEND_URL']))

  db.init_app(app)

  from Hinkskalle.util.jobs import rq, setup_cron
  
  if 'HINKSKALLE_REDIS_URL' in os.environ:
    app.config['RQ_REDIS_URL'] = os.environ.get('HINKSKALLE_REDIS_URL')
  rq.init_app(app)

  app.config['ENABLE_REGISTER'] = os.environ.get('HINKSKALLE_ENABLE_REGISTER', app.config.get('ENABLE_REGISTER', False))
  app.config['SINGULARITY_FLAVOR'] = os.environ.get('HINKSKALLE_SINGULARITY_COMMAND', app.config.get('SINGULARITY_FLAVOR', 'singularity'))
  app.config['DEFAULT_USER_QUOTA'] = os.environ.get('HINKSKALLE_DEFAULT_USER_QUOTA', app.config.get('DEFAULT_USER_QUOTA', 0))
  app.config['DEFAULT_GROUP_QUOTA'] = os.environ.get('HINKSKALLE_DEFAULT_GROUP_QUOTA', app.config.get('DEFAULT_GROUP_QUOTA', 0))

  app.url_map.converters['distname']=OrasNameConverter 
  generator.register_flask_converter_to_swagger_type('distname', 'path')


  with app.app_context():
    import Hinkskalle.routes
    import Hinkskalle.commands
    # make sure init_app is called after importing routes??
    rebar.init_app(app)

    # see https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722
    migrate.init_app(app, db, render_as_batch=db.engine.url.drivername == 'sqlite')
    #migrate_up()


  # log config has to be done after migrate_up, see 
  # https://github.com/miguelgrinberg/Flask-Migrate/issues/227
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
        },
      }
  })

  password_checkers.init_app(app)
  setup_cron(app)

  return app

if __name__ == '__main__':
  app=create_app()
  app.run()
