from flask import Flask
from flask_rebar import Rebar
from logging.config import dictConfig
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate, upgrade as migrate_up

import os

rebar = Rebar()

registry = rebar.create_handler_registry(prefix="/")
registry.set_default_authenticator(None)

from Hinkskalle.util.swagger import register_authenticators
register_authenticators(registry)

from Hinkskalle.util.auth.token import TokenAuthenticator
authenticator = TokenAuthenticator()

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

from Hinkskalle.util.auth import PasswordAuthenticators
password_checkers=PasswordAuthenticators()

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
  if not 'AUTH' in app.config:
    app.config['AUTH']={}

  if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI']=os.environ['SQLALCHEMY_DATABASE_URI']
  app.config['PREFERRED_URL_SCHEME']=os.environ.get('PREFERRED_URL_SCHEME', 'http')

  ldap_conf = {}
  for key in ['HOST', 'PORT', 'BIND_DN', 'BIND_PASSWORD', 'BASE_DN']:
    if 'HINKSKALLE_LDAP_' + key in os.environ:
      ldap_conf[key]=os.environ.get('HINKSKALLE_LDAP_'+key)
  if len(ldap_conf) > 0:
    app.config['AUTH']['LDAP'] = app.config['AUTH'].get('LDAP', {})
    for k, v in ldap_conf.items():
      app.config['AUTH']['LDAP'][k]=v


  db.init_app(app)
  migrate.init_app(app, db)

  with app.app_context():
    import Hinkskalle.commands
    import Hinkskalle.routes
    # make sure init_app is called after importing routes??
    rebar.init_app(app)

    # see https://github.com/miguelgrinberg/Flask-Migrate/issues/61#issuecomment-208131722
    migrate.init_app(app, db, render_as_batch=db.engine.url.drivername == 'sqlite')
    migrate_up()
  
  password_checkers.init_app(app)

  return app

if __name__ == '__main__':
  app=create_app()
  app.run()
