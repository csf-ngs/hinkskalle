import typing
import hashlib
import tempfile

from Hinkskalle.models.User import GroupRoles, User, Group, UserGroup
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models.Container import Container
from Hinkskalle.models.Image import Image, UploadStates
from Hinkskalle import db

default_entity_name = 'test-hase'

def _create_user(name='test.hase', is_admin=False) -> User:
  firstname, lastname = name.split('.')
  user = User(username=name, email=name+'@ha.se', firstname=firstname, lastname=lastname, is_admin=is_admin)
  db.session.add(user)
  db.session.commit()
  return user

def _create_group(name='Testhasenstall', **kwargs) -> Group:
  group = Group(name=name, email=name+'@ha.se', **kwargs)
  db.session.add(group)
  db.session.commit()
  return group

def _set_member(user: User, group: Group, role=GroupRoles.contributor) -> UserGroup:
  ug = UserGroup(user=user, group=group, role=role)
  db.session.add(ug)
  db.session.commit()
  return ug

def _create_collection(name='test-collection') -> typing.Tuple[Collection, Entity]:
  try:
    entity = Entity.query.filter_by(name=default_entity_name).one()
  except:
    entity = Entity(name=default_entity_name)
    db.session.add(entity)
    db.session.commit()


  coll = Collection(name=name, entity_id=entity.id)
  db.session.add(coll)
  db.session.commit()
  return coll, entity

def _create_container(postfix: str ='container') -> typing.Tuple[Container, Collection, Entity]:
  coll, entity = _create_collection(f"test-collection-{postfix}")

  container = Container(name=f"test-{postfix}", collection_id=coll.id)
  db.session.add(container)
  db.session.commit()
  return container, coll, entity

def _create_image(hash: str='sha256.oink', postfix: str='container', uploadState: UploadStates=UploadStates.initialized, **kwargs) -> typing.Tuple[Image, Container, Collection, Entity]:
  try:
    coll = Collection.query.filter_by(name=f"test-coll-{postfix}").one()
    entity = coll.entity_ref
  except:
    coll, entity = _create_collection(f"test-coll-{postfix}")

  try:
    container = Container.query.filter_by(name=f"test-{postfix}").one()
  except:
    container = Container(name=f"test-{postfix}", collection_ref=coll)
    db.session.add(container)
    db.session.commit()

  image = Image(container_ref=container, hash=hash, uploadState=uploadState, **kwargs)
  db.session.add(image)
  db.session.commit()
  return image, container, coll, entity

def _prepare_img_data(data=b"Hello Dorian!") -> typing.Tuple[bytes, str]:
    img_data=data
    m = hashlib.sha256()
    m.update(img_data)
    return img_data, f"sha256.{m.hexdigest()}"

def _fake_img_file(image: Image, data=b"Hello Dorian!"):
    tmpf = tempfile.NamedTemporaryFile()
    tmpf.write(data)
    tmpf.flush()
    image.location=tmpf.name
    image.size=len(data)
    image.uploadState=UploadStates.completed
    db.session.commit()
    return tmpf

