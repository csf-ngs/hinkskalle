from abc import ABC, abstractmethod
from jinja2 import Environment, PackageLoader

class TypescriptRenderer(ABC):
  def __init__(self):
    self.loader = PackageLoader('Hinkskalle.util.typescript', 'templates')
    self.env = Environment(loader=self.loader)

  @abstractmethod
  def render(self, defs):
    pass
