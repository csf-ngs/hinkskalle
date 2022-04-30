import re

def validate_name(data: dict, key: str = 'name') -> dict:
    errors = {}
    if data.get(key, '') != '':
      try:
        validate_as_name(data[key])
      except ValueError as e:
        errors[key] = str(e)
    return errors

def validate_as_name(name: str):
    if not re.match(r"^[a-zA-Z0-9\.\-_]+$", name):
      raise ValueError(f"name contains invalid characters")
    if re.match(r"^[\.\-_]", name) or re.match(r".*[\.\-_]$", name):
      raise ValueError(f"name must start and end with a letter or number")