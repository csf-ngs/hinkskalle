
from Hinkskalle.models.Manifest import Manifest
from Hinkskalle.models.Tag import Tag
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
import datetime
from sqlalchemy import update
from Hinkskalle.models import Container, Image
from Hinkskalle import db

from ..route_base import RouteBase
from .._util import _create_container, _create_collection
class TestContainers(RouteBase):
  def test_list_noauth(self):
    ret = self.client.get('/v1/containers/what/ever')
    self.assertEqual(ret.status_code, 401)

  def test_list(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container2.collection_ref=coll
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIsInstance(json, list)
    self.assertEqual(len(json), 2)
    self.assertListEqual([ c['name'] for c in json ], [ container1.name, container2.name ] )
  
  def test_list_user(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container1.owner=self.user
    container2.owner=self.user
    container2.collection_ref=coll
    coll.owner=self.user
    entity.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container1.name, container2.name ])

  def test_list_user_default(self):
    container1, coll, entity = _create_container('cont1')
    container2, _, _ = _create_container('cont2')
    container1.owner=self.user
    container2.owner=self.user
    coll.owner=self.user
    entity.name='default'
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/default/{coll.name}")
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertListEqual([ c['name'] for c in json ], [ container1.name ])
  
  def test_list_user_other(self):
    _, coll, entity = _create_container('coll1')
    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}")
    self.assertEqual(ret.status_code, 403)

  def test_get_noauth(self):
    ret = self.client.get('/v1/containers/what/ev/er')
    self.assertEqual(ret.status_code, 401)

  def test_get(self):
    container, coll, entity = _create_container()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))
  
  def test_get_case(self):
    container = _create_container()[0]
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/Test-Hase/test-Collection-Container/Test-Container")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data').get('id'), str(container.id)) # type: ignore
  
  def test_get_case_legacy(self):
    container, collection, entity = _create_container()
    db.session.execute(update(Entity).where(Entity.id==entity.id).values(name='TeStHaSe'))
    db.session.execute(update(Collection).where(Collection.id==collection.id).values(name='TeStHaSe'))
    db.session.execute(update(Container).where(Container.id==container.id).values(name='OiNk'))
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/TeSthase/TeStHaSe/OiNk")
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data').get('id'), str(container.id)) # type: ignore
  
  def test_get_default_entity(self):
    container, coll, entity = _create_container()
    entity.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers//{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/{coll.name}/{container.name}") # type: ignore

    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))
  
  def test_get_default_collection(self):
    container, coll, entity = _create_container()
    coll.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}//{container.name}")
    self.assertEqual(ret.status_code, 308)
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/{entity.name}/default/{container.name}$") # type: ignore
    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))

  def test_get_default_collection_default_entity(self):
    container, coll, entity = _create_container()
    entity.name='default'
    coll.name='default'
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers///{container.name}")
    self.assertEqual(ret.status_code, 308, 'triple slash')
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default//{container.name}$") # type: ignore
    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 308, 'triple slash')
    self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/default/{container.name}$") # type: ignore

    with self.fake_admin_auth():
      ret = self.client.get(ret.headers.get('Location'))
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))

    # double slash expansion gives an ambigous route (collides with list containers)
    # maybe we get by without it
    # with self.fake_admin_auth():
    #   ret = self.client.get(f"/v1/containers//{container.name}")
    # self.assertEqual(ret.status_code, 308, 'double slash')
    # self.assertRegex(ret.headers.get('Location', None), rf"/v1/containers/default/{container.name}$")

    # with self.fake_admin_auth():
    #   ret = self.client.get(ret.headers.get('Location'))
    # self.assertEqual(ret.status_code, 200)
    # data = ret.get_json().get('data') # type: ignore
    # self.assertEqual(data['id'], str(container.id))

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/containers/{container.name}")
    self.assertEqual(ret.status_code, 200, 'single slash')
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))

  def test_get_user(self):
    container, coll, entity = _create_container()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['id'], str(container.id))

  def test_get_user_other_own_collection(self):
    container, coll, entity = _create_container()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)

  def test_get_user_other(self):
    container, coll, entity = _create_container()
    entity.owner=self.other_user
    coll.owner=self.other_user
    container.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.get(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 403)

  def test_create(self):
    coll, _ = _create_collection()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['collection'], str(coll.id))
    self.assertEqual(data['createdBy'], self.admin_username)
  
  def test_create_singularity(self):
    coll, _ = _create_collection()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'deleted': False, 
        'createdBy': '', 
        'createdAt': '0001-01-01T00:00:00Z', 
        'updatedAt': '0001-01-01T00:00:00Z', 
        'deletedAt': '0001-01-01T00:00:00Z', 
        'id': '', 
        'name': 'alpine', 
        'description': 'No description', 
        'fullDescription': '', 
        'collection': str(coll.id), 
        'images': None, 
        'imageTags': None, 
        'archTags': None, 
        'size': 0, 
        'downloadCount': 0, 
        'stars': 0, 
        'private': False, 
        'readOnly': False, 
        'customData': ''
    })
    self.assertEqual(ret.status_code, 200)
  
  def test_create_sticky(self):
    coll, entity = _create_collection()
    entity.owner = self.user
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    self.assertEqual(data['collection'], str(coll.id))
    self.assertEqual(data['createdBy'], self.username)

  def test_create_check_name(self):
    coll = _create_collection()[0]

    for fail in ['Babsi Streusand', '-oink', 'Babsi&Streusand', 'oink-']:
      with self.fake_admin_auth():
          ret = self.client.post('/v1/containers', json={
            'name': fail,
            'collection': str(coll.id),
          })
      self.assertEqual(ret.status_code, 400)
  
  def test_create_private(self):
    coll, _ = _create_collection()
    coll.private = True
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    dbContainer = Container.query.get(data['id'])
    self.assertTrue(dbContainer.private)

    coll2, _ = _create_collection('no-private')
    coll2.private = False
    db.session.commit()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'auch.oink',
        'collection': str(coll2.id),
      })
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data') # type: ignore
    dbContainer = Container.query.get(data['id'])
    self.assertFalse(dbContainer.private)





  def test_create_not_unique(self):
    container, coll, _ = _create_container()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': container.name,
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 412)

  def test_create_not_unique_case(self):
    container, coll, _ = _create_container()
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': container.name.upper(),
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 412)
  
  def test_invalid_collection(self):
    with self.fake_admin_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': -666,
      })
    self.assertEqual(ret.status_code, 400)
  
  def test_create_user(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    coll.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 200)

  def test_create_user_other(self):
    coll, entity = _create_collection()
    entity.owner=self.user
    coll.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post('/v1/containers', json={
        'name': 'oink',
        'collection': str(coll.id),
      })
    self.assertEqual(ret.status_code, 403)
  
  def test_update(self):
    container, coll, entity = _create_container()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
        'fullDescription': 'Der hot Drei Eckn',
        'private': True,
        'readOnly': True,
        'vcsUrl': 'http://da.ham',
      })
    
    self.assertEqual(ret.status_code, 200)

    dbContainer = Container.query.filter(Container.name==container.name).one()
    self.assertEqual(dbContainer.description, 'Mei Huat')
    self.assertEqual(dbContainer.fullDescription, 'Der hot Drei Eckn')
    self.assertTrue(dbContainer.private)
    self.assertTrue(dbContainer.readOnly)
    self.assertEqual(dbContainer.vcsUrl, 'http://da.ham')

    self.assertTrue(abs(dbContainer.updatedAt - datetime.datetime.now()) < datetime.timedelta(seconds=2))
  
  def test_update_dumponly(self):
    container, coll, entity = _create_container('grunz')
    container_id = container.id
    coll_id = coll.id
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'name': 'oink',
        'collection': '23',
      })
    self.assertEqual(ret.status_code, 200)
    dbContainer: Container = Container.query.get(container_id)
    self.assertEqual(dbContainer.name, 'test-grunz')
    self.assertEqual(dbContainer.collection, coll_id)
  

  
  def test_update_case(self):
    container = _create_container()[0]

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/containers/Test-Hase/test-Collection-Container/Test-Container", json={
        'description': 'Mei Huat',
      })
    self.assertEqual(ret.status_code, 200)
    dbContainer = Container.query.get(container.id)
    self.assertEqual(dbContainer.description, 'Mei Huat')
    
  def test_update_owner(self):
    container, coll, entity = _create_container()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'createdBy': self.other_username
      })
    
    self.assertEqual(ret.status_code, 200)
    dbContainer = Container.query.filter(Container.name==container.name).one()
    self.assertEqual(dbContainer.createdBy, self.other_username)

  def test_update_user(self):
    container, coll, entity = _create_container()
    container.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
        'fullDescription': 'Der hot Drei Eckn',
        'private': True,
        'readOnly': True,
        'vcsUrl': 'http://da.ham',
      })
    
    self.assertEqual(ret.status_code, 200)
    
  def test_update_user_owner(self):
    container, coll, entity = _create_container()
    container.owner = self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'createdBy': self.other_username
      })
    
    self.assertEqual(ret.status_code, 403)
    dbContainer = Container.query.filter(Container.name==container.name).one()
    self.assertEqual(dbContainer.createdBy, self.username)

    with self.fake_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'createdBy': self.username
      })
    
    self.assertEqual(ret.status_code, 200)

  def test_update_user_other(self):
    container, coll, entity = _create_container()
    container.owner=self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v1/containers/{entity.name}/{coll.name}/{container.name}", json={
        'description': 'Mei Huat',
      })
    
    self.assertEqual(ret.status_code, 403)

  def test_delete(self):
    container, coll, entity = _create_container()

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Container.query.filter(Container.name==container.name).first())

  def test_delete_case(self):
    container = _create_container()[0]
    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/containers/Test-Hase/test-Collection-Container/Test-Container")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Container.query.filter(Container.name==container.name).first())
  
  def test_delete_not_empty(self):
    container, coll, entity = _create_container()
    image = Image(hash="test-conti1", container_id=coll.id)
    db.session.add(image)
    db.session.commit()


    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 412)
  
  def test_delete_cascade(self):
    container, coll, entity = _create_container()
    image = Image(hash="test-conti1", container_id=coll.id)
    db.session.add(image)
    db.session.commit()
    image_id = image.id
    tag = container.tag_image('v1', image.id)
    tag_id = tag.id
    manifest = image.generate_manifest()
    manifest_id = manifest.id

    with self.fake_admin_auth():
      ret = self.client.delete(f"/v1/containers/{entity.name}/{coll.name}/{container.name}?cascade=1")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Container.query.filter(Container.name==container.name).first())
    self.assertIsNone(Tag.query.get(tag_id))
    self.assertIsNone(Manifest.query.get(manifest_id))
    self.assertIsNone(Image.query.get(image_id))

  def test_delete_user(self):
    container, coll, entity = _create_container()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.delete(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 200)

    self.assertIsNone(Container.query.filter(Container.name==container.name).first())

  def test_delete_user_other(self):
    container, coll, entity = _create_container()
    entity.owner=self.user
    db.session.commit()
    coll.owner=self.other_user
    db.session.commit()
    container.owner=self.other_user

    with self.fake_auth():
      ret = self.client.delete(f"/v1/containers/{entity.name}/{coll.name}/{container.name}")
    self.assertEqual(ret.status_code, 403)

  def test_delete_noauth(self):
    ret = self.client.delete("/v1/containers/oi/nk/grunz")
    self.assertEqual(ret.status_code, 401)