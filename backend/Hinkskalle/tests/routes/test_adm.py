from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.models import Adm, AdmKeys
from Hinkskalle import db

class TestAdm(RouteBase):
  def test_get_noauth(self):
    ret = self.client.get('/v1/adm/oink')
    self.assertEqual(ret.status_code, 401)
  
  def test_get_user(self):
    with self.fake_auth():
      ret = self.client.get('/v1/adm/oink')
    self.assertEqual(ret.status_code, 403)

  def test_put_noauth(self):
    ret = self.client.put('/v1/adm/oink', json={})
    self.assertEqual(ret.status_code, 401)
  
  def test_put_user(self):
    with self.fake_auth():
      ret = self.client.put('/v1/adm/oink', json={})
    self.assertEqual(ret.status_code, 403)

  def test_get(self):
    key = Adm(key=AdmKeys.ldap_sync_results, val={ 'oi': 'nk' })
    db.session.add(key)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/adm/{AdmKeys.ldap_sync_results.name}")
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual(ret.get_json().get('data'), { 'key': AdmKeys.ldap_sync_results.name, 'val': { 'oi': 'nk' }})
  
  def test_get_invalid(self):
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/adm/oink")
    self.assertEqual(ret.status_code, 404)
  
  def test_update(self):
    key = Adm(key=AdmKeys.ldap_sync_results, val={ 'oi': 'nk' })
    db.session.add(key)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/adm/{AdmKeys.ldap_sync_results.name}", json={ 'val': { 'gru': 'nz' }})
    self.assertEqual(ret.status_code, 200)

    db_key = Adm.query.get(AdmKeys.ldap_sync_results)
    self.assertDictEqual(db_key.val, { 'gru': 'nz' })
    self.assertDictEqual(ret.get_json().get('data').get('val'), { 'gru': 'nz' })
  
  def test_update_new(self):
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/adm/{AdmKeys.ldap_sync_results.name}", json={ 'val': { 'gru': 'nz' }})
    self.assertEqual(ret.status_code, 200)

    db_key = Adm.query.get(AdmKeys.ldap_sync_results)
    self.assertDictEqual(db_key.val, { 'gru': 'nz' })
    self.assertDictEqual(ret.get_json().get('data').get('val'), { 'gru': 'nz' })

  def test_update_invalid(self):
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/adm/oink", json={ 'val': { 'gru': 'nz' }})
    self.assertEqual(ret.status_code, 400)
