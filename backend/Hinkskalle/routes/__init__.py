
import Hinkskalle.routes.base
import Hinkskalle.routes.auth
import Hinkskalle.routes.entities
import Hinkskalle.routes.collections
import Hinkskalle.routes.containers
import Hinkskalle.routes.images
import Hinkskalle.routes.imagefiles
import Hinkskalle.routes.tags
import Hinkskalle.routes.search
import Hinkskalle.routes.shub
import Hinkskalle.routes.oras

import Hinkskalle.routes.users
import Hinkskalle.routes.tokens

import Hinkskalle.routes.adm


def _get_service_url():
  from flask import request, current_app
  service_url = request.url_root.rstrip('/')
  if current_app.config.get('PREFERRED_URL_SCHEME', 'http') == 'https':
    service_url = service_url.replace('http:', 'https:')
  return service_url

