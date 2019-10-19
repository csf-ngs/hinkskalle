from flask_mongoengine import MongoEngine

from Hinkskalle.models.Tag import *
from Hinkskalle.models.Image import *
from Hinkskalle.models.Entity import *
from Hinkskalle.models.Collection import *
from Hinkskalle.models.Container import *

db = MongoEngine()