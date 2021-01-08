from Hinkskalle.routes.base import *
from Hinkskalle.routes.auth import *
from Hinkskalle.routes.entities import *
from Hinkskalle.routes.collections import *
from Hinkskalle.routes.containers import *
from Hinkskalle.routes.images import *
from Hinkskalle.routes.imagefiles import *
from Hinkskalle.routes.tags import *
from Hinkskalle.routes.search import *
from Hinkskalle.routes.shub import *

from Hinkskalle.routes.users import *
from Hinkskalle.routes.tokens import *

from Hinkskalle.routes.adm import *

from flask import request, current_app
def _get_service_url():
  service_url = request.url_root.rstrip('/')
  if current_app.config.get('PREFERRED_URL_SCHEME', 'http') == 'https':
    service_url = service_url.replace('http:', 'https:')
  return service_url

