import typing
from ..route_base import RouteBase

from Hinkskalle.models import Adm, AdmKeys
from Hinkskalle import db

from ..utils.test_ldap import MockLDAP
from unittest import mock

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
    for slot in AdmKeys:
      key = Adm(key=slot, val={ 'oi': 'nk' })
      db.session.add(key)
      db.session.commit()

      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/adm/{slot.name}")
      self.assertEqual(ret.status_code, 200, msg=f"get {slot.name}")
      self.assertDictEqual(ret.get_json().get('data'), { 'key': slot.name, 'val': { 'oi': 'nk', 'scheduled': mock.ANY }})
  
  def test_get_invalid(self):
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/adm/oink")
    self.assertEqual(ret.status_code, 404)
  
  def test_update(self):
    for slot in AdmKeys:
      key = Adm(key=slot, val={ 'oi': 'nk' })
      db.session.add(key)
      db.session.commit()

      with self.fake_admin_auth():
        ret = self.client.put(f"/v1/adm/{slot.name}", json={ 'val': { 'gru': 'nz' }})
      self.assertEqual(ret.status_code, 200, msg=f"put {slot.name}")

      db_key = Adm.query.get(slot)
      self.assertDictEqual(db_key.val, { 'gru': 'nz' })
      self.assertDictEqual(ret.get_json().get('data').get('val'), { 'gru': 'nz' })
  
  def test_update_new(self):
    for slot in AdmKeys:
      with self.fake_admin_auth():
        ret = self.client.put(f"/v1/adm/{slot.name}", json={ 'val': { 'gru': 'nz' }})
      self.assertEqual(ret.status_code, 200, msg=f"put {slot.name} create")

      db_key = Adm.query.get(slot)
      self.assertDictEqual(db_key.val, { 'gru': 'nz' })
      self.assertDictEqual(ret.get_json().get('data').get('val'), { 'gru': 'nz' })

  def test_update_invalid(self):
    with self.fake_admin_auth():
      ret = self.client.put(f"/v1/adm/oink", json={ 'val': { 'gru': 'nz' }})
    self.assertEqual(ret.status_code, 400)

  def test_ldap_sync(self):
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/ldap/sync")

    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertDictContainsSubset({
      'status': 'queued',
      'funcName': 'Hinkskalle.util.jobs.sync_ldap'
    }, data)
  
  def test_ldap_sync_user(self):
    with self.fake_auth():
      ret = self.client.post(f"/v1/ldap/sync")
    self.assertEqual(ret.status_code, 403)
  
  def test_start_task(self):
    from Hinkskalle.util.jobs import adm_map

    for slot in AdmKeys:
      with self.fake_admin_auth():
        ret = self.client.post(f"/v1/adm/{slot.name}/run")
      self.assertEqual(ret.status_code, 200, msg=f"start job {slot}")
      data = ret.get_json().get('data')
      self.assertDictContainsSubset({
        'status': 'queued',
        'funcName': f"Hinkskalle.util.jobs.{adm_map[slot.name].__name__}"
      }, data)

  def test_start_task_invalid(self):
    with self.fake_admin_auth():
      ret = self.client.post(f"/v1/adm/oink/run")
    self.assertEqual(ret.status_code, 406)
  
  def test_start_task_user(self):
    with self.fake_auth():
      ret = self.client.post(f"/v1/adm/{AdmKeys.ldap_sync_results}/run")
    self.assertEqual(ret.status_code, 403)
  def test_start_task_noauth(self):
    ret = self.client.post(f"/v1/adm/{AdmKeys.ldap_sync_results}/run")
    self.assertEqual(ret.status_code, 401)

  
  def test_ldap_ping(self):
    mock_ldap = MockLDAP()
    def _get_auth(app=None):
      return mock_ldap.auth
    
    with mock.patch('Hinkskalle.util.auth.ldap.LDAPUsers', new=_get_auth):
      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/ldap/ping")
    
    self.assertEqual(ret.status_code, 200)
    self.assertDictEqual({
      'status': 'ok',
    }, ret.get_json().get('data'))

  def test_ldap_ping_wrong_password(self):
    mock_ldap = MockLDAP()
    def _get_auth(app=None):
      return mock_ldap.auth
    
    mock_ldap.svc.bind_password='failfalsch'
    with mock.patch('Hinkskalle.util.auth.ldap.LDAPUsers', new=_get_auth):
      with self.fake_admin_auth():
        ret = self.client.get(f"/v1/ldap/ping")
    
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['status'], 'failed')
    self.assertRegex(data['error'], r'^LDAPInvalidCredentialsResult')
  
  def test_ldap_ping_user(self):
    with self.fake_auth():
      ret = self.client.get(f"/v1/ldap/ping")
    self.assertEqual(ret.status_code, 403)
  
  def test_ldap_status_disabled(self):
    self.app.config['AUTH']['LDAP']={}
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/ldap/status")
    
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['status'], 'disabled')

  def test_ldap_status_enabled(self):
    self.app.config['AUTH']['LDAP'] = {
      'HOST': 'dum.my',
      'BASE_DN': 'ou=test',
      'BIND_DN': 'cn=chef,ou=test',
      'BIND_PASSWORD': 'dontleakme',
    }
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/ldap/status")
    
    self.assertEqual(ret.status_code, 200)
    data = ret.get_json().get('data')
    self.assertEqual(data['status'], 'configured')
    self.assertDictEqual(data['config'], {
      'HOST': 'dum.my',
      'BASE_DN': 'ou=test',
      'BIND_DN': 'cn=chef,ou=test'
    })
  
  def test_ldap_status_user(self):
    with self.fake_auth():
      ret = self.client.get(f"/v1/ldap/status")
    self.assertEqual(ret.status_code, 403)

  
  def test_get_job(self):
    from Hinkskalle.util.jobs import sync_ldap
    job = sync_ldap.queue()
    with self.fake_admin_auth():
      ret = self.client.get(f"/v1/jobs/{job.id}")
    self.assertEqual(ret.status_code, 200)
  
  def test_get_job_user(self):
    with self.fake_auth():
      ret = self.client.get(f"/v1/jobs/oink")
    self.assertEqual(ret.status_code, 403)