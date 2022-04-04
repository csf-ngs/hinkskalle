from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes
from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema, ValidationError
from sqlalchemy.orm.exc import NoResultFound # type: ignore
from sqlalchemy.exc import IntegrityError
from flask import request, current_app, g
import os.path
import os

from Hinkskalle.models import Tag, Container, Image

class TagResponseSchema(ResponseSchema):
  data = fields.Dict()

class TagUpdateSchema(RequestSchema):
  pass

def _get_container(container_id, update=False):
  try:
    container = Container.query.filter(Container.id==container_id).one()
  except NoResultFound:
    raise errors.NotFound(f"container {container_id} not found")
  if update:
    if not container.check_update_access(g.authenticated_user):
      raise errors.Forbidden(f"access denied.")
  else:
    if not container.check_access(g.authenticated_user):
      raise errors.Forbidden(f"access denied.")
  return container


@registry.handles(
  rule='/v1/tags/<string:container_id>',
  method='GET',
  response_body_schema=TagResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
)
def get_tags(container_id):
  return { 'data': _get_container(container_id).imageTags }

@registry.handles(
  rule='/v2/tags/<string:container_id>',
  method='GET',
  response_body_schema=TagResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
)
def get_tags_v2(container_id):
  return { 'data': _get_container(container_id).archImageTags }

@registry.handles(
  rule='/v2/tags/<string:container_id>',
  method='POST',
  response_body_schema=TagResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user) # type: ignore
)
def update_tag_v2(container_id):
  container = _get_container(container_id, update=True)

  tags = request.get_json(force=True)
  if tags is None:
    raise Exception("Invalid json")
  if 'Tag' in tags and 'ImageID' in tags and 'Arch' in tags:
    tags = {
      tags['Arch']: {
        tags['Tag']: tags['ImageID']
      }
    }

  for arch, arch_tags in tags.items():
    for tag_name, tag_image in arch_tags.items():
      if not tag_image:
        current_app.logger.debug(f"removing tag {tag_name}/{arch}...")
        for image in container.images_ref.filter(Image.arch == arch):
          for tag in image.tags_ref:
            if tag.name == tag_name.lower():
              db.session.delete(tag)
      else:
        try:
          new_tag = container.tag_image(tag_name, tag_image, arch=arch)
          new_tag.image_ref.arch=arch
        except NoResultFound:
          raise errors.NotFound(f"Image {tag_image} not found for container {container_id}")
        except IntegrityError:
          raise errors.NotFound(f"Invalid image id {tag_image} not found for container {container_id}")
        except ValidationError as err:
          raise errors.BadRequest(err.messages.get('name', 'Unknown validation error')) # type: ignore

        current_app.logger.debug(f"created tag {new_tag.name}/{arch} on {new_tag.image_ref.id}")
        _link_tag(new_tag)

  db.session.commit()
  return { 'data': container.archImageTags }


@registry.handles(
  rule='/v1/tags/<string:container_id>',
  method='POST',
  response_body_schema=TagResponseSchema(),
  authenticators=authenticator.with_scope(Scopes.user), # type: ignore
)
def update_tag(container_id):
  container = _get_container(container_id, update=True)

  tag = request.get_json(force=True)
  if tag is None:
    raise Exception("Invalid json")
  # why do you have a versioned API when you change
  # the data structure and send it to the same
  # endpoint???
  if 'Tag' in tag and 'ImageID' in tag:
    tag = {
      tag['Tag']: tag['ImageID']
    }
  
  for tag_name, tag_image in tag.items():
    if not tag_image:
      current_app.logger.debug(f"removing tag {tag_name}...")
      for image in container.images_ref:
        for tag in image.tags_ref:
          if tag.name == tag_name.lower():
            db.session.delete(tag)
    else:
      try:
        new_tag = container.tag_image(tag_name, tag_image)
      except NoResultFound:
        raise errors.NotFound(f"Image {tag_image} not found for container {container_id}")
      except IntegrityError:
        raise errors.NotFound(f"Invalid image id {tag_image} not found for container {container_id}")
      except ValidationError as err:
        raise errors.BadRequest(err.messages.get('name', 'Unknown validation error')) # type: ignore

      current_app.logger.debug(f"created tag {new_tag.name} on {new_tag.image_ref.id}")
      _link_tag(new_tag)


  db.session.commit()
  return { 'data': container.imageTags }

def _link_tag(new_tag):
  image=new_tag.image_ref
  if image.uploaded and os.path.exists(image.location):
    subdir = image.collectionName if image.entityName == 'default' else os.path.join(image.entityName, image.collectionName)
    if image.arch:
      subdir = os.path.join(image.arch, subdir)
    target = os.path.join(current_app.config["IMAGE_PATH"], subdir, f"{image.containerName}_{new_tag.name}.sif")
    current_app.logger.debug(f"Creating link {image.location}->{target}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.lexists(target):
      current_app.logger.debug(f"... removing existing {target}")
      os.remove(target)
    os.link(image.location, target)
  else:
    current_app.logger.warning(f"Tagged image {image.id} which was not uploaded or does not exist!")






