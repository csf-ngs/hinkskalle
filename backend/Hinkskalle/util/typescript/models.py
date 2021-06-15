from jinja2.exceptions import TemplateNotFound

from flask import current_app
from Hinkskalle.util.typescript.base import TypescriptRenderer

import shutil
import os.path

class ModelRenderer(TypescriptRenderer):
  default_template = '_class.ts.tpl'
  models_template = 'models.ts.tpl'

  def render(self, definitions):
    class_defs = []
    # since Agent inherits from User it must be declared after User!
    # XXX flask_rebar bug:
    # see https://github.com/plangrid/flask-rebar/issues/90
    for classname in ['Collection', 'Container', 'Entity', 'Image', 'Group', 'User', 'Token', 'Job', 'LdapStatus', 'LdapPing', 'Manifest']:
      schema_name = f"{classname}Schema"
      if not schema_name in definitions:
        raise Exception(f"Schema {schema_name} for {classname} not in swagger defs")
      # current_app.logger.debug(definitions[schema_name])
      current_app.logger.debug(f"Rendering {classname}...")
      class_defs.append(self.render_class(classname, definitions[schema_name]))
    
    current_app.logger.debug(f"Rendering allmodels...")
    template = self.env.get_template(self.models_template)
    return template.render(models=class_defs)

  
  def render_class(self, classname, schema):
    def field_def(prop_def):
      field = { 'name': prop, 'is_reference': False, 'readonly': False, 'multi': False }
      if '$ref' in prop_def:
        ref = prop_def['$ref'].replace('#/definitions/', '').replace('Schema', '')
        field['type'] = ref
        field['is_reference'] = True
      elif prop_def.get('format', None) == 'date-time':
        field['type'] = 'Date | null'
      elif prop_def['type'] == 'integer':
        field['type'] = 'number'
      elif prop_def['type'] == 'object':
        field['type'] = 'any'
      elif prop_def['type'] == 'array':
        ndef = field_def(prop_def['items'])
        field['multi'] = True
        field['is_reference'] = ndef['is_reference']
        field['type'] = ndef['type']
        field['readonly'] = ndef['readonly']
      else:
        field['type'] = prop_def['type']

      if prop_def.get('readOnly', False):
        field['readonly'] = True
      return field

    template_name = f"{classname}.ts.tpl"
    try:
      template = self.env.get_template(template_name)
    except TemplateNotFound:
      _, fullpath, _ = self.loader.get_source(self.env, self.default_template)
      shutil.copyfile(fullpath, os.path.join(os.path.dirname(fullpath), template_name))
      template = self.env.get_template(template_name)

    fields=[]
    for prop in schema['properties']:
      field = field_def(schema['properties'][prop])
      fields.append(field)

    return template.render(classname=classname, fields=fields)