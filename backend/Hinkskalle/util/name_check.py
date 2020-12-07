import re

def validate_name(data):
    errors = {}
    if 'name' in data and data['name'] != '':
      if not re.match(r"^[a-zA-Z0-9\.\-_]+$", data['name']):
        errors['name']=f"name contains invalid characters"
      if re.match(r"^[\.\-_]", data['name']) or re.match(r".*[\.\-_]$", data['name']):
        errors['name']='name must start and end with a letter or number'
    return errors