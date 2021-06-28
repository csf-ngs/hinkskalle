import store from '@/store';
import {LdapStatus, plainToLdapStatus, LdapPing, plainToLdapPing, plainToAdmLdapSyncResults, Job, plainToJob} from '@/store/models';

import axios from 'axios';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;
store.state.backend = mockAxios;

const makeTestStatus = (): LdapStatus => ({
  status: 'configured',
  config: { oi: 'nk' },
});
const makeTestStatusObj = (): LdapStatus => {
  return plainToLdapStatus(makeTestStatus());
}

const makeTestPing = (): LdapPing => ({
  status: 'ok',
  error: '',
});
const makeTestPingObj = (): LdapPing => {
  return plainToLdapPing(makeTestPing());
}

describe('adm store getters', () => {
  it('has status getter', () => {
    store.state.adm!.status = 'loading';
    expect(store.getters['adm/status']).toBe('loading');
  });
  it('has ldap status getter', () => {
    const testStatus = makeTestStatusObj();
    store.state.adm!.ldapStatus = testStatus;
    expect(store.getters['adm/ldapStatus']).toStrictEqual(testStatus);
  });
  it('has ldap ping response getter', () => {
    const testPing = makeTestPingObj();
    store.state.adm!.ldapPingResponse = testPing;
    expect(store.getters['adm/ldapPing']).toStrictEqual(testPing);
  })
});

describe('adm mutations', () => {
  it('has status mutations', () => {
    store.state.users!.status = '';
    store.commit('adm/loading');
    expect(store.state.adm!.status).toBe('loading');
    store.commit('adm/succeeded');
    expect(store.state.adm!.status).toBe('success');
    store.commit('adm/failed');
    expect(store.state.adm!.status).toBe('failed');
  });
});

describe('adm actions', () => {
  it('has get ldap status', done => {
    store.state.adm!.ldapStatus = null;
    mockAxios.get.mockResolvedValue({ data: { data: makeTestStatus() }});

    const promise = store.dispatch('adm/ldapStatus');
    expect(store.state.adm!.status).toBe('loading');
    promise.then(ret => {
      expect(mockAxios.get).toHaveBeenCalledWith(`/v1/ldap/status`);
      expect(store.state.adm!.ldapStatus).toStrictEqual(makeTestStatusObj());
      done();
    });
  });

  it('does not refresh ldap status', done => {
    const testStatusObj = makeTestStatusObj();
    store.state.adm!.ldapStatus = testStatusObj;
    mockAxios.get.mockReset();
    mockAxios.get.mockResolvedValue({});
    store.dispatch('adm/ldapStatus')
      .then(ret => {
        expect(ret).toBe(testStatusObj);
        expect(store.state.adm!.ldapStatus).toBe(testStatusObj);
        expect(mockAxios.get).toHaveBeenCalledTimes(0);
        done();
      });
  });

  it('refreshes ldap status on demand', done => {
    store.state.adm!.ldapStatus = makeTestStatusObj();
    const newStatus = makeTestStatus();
    newStatus.status = 'failed';
    mockAxios.get.mockResolvedValue({ data: { data: newStatus }});

    store.dispatch('adm/ldapStatus', { reload: true })
      .then(ret => {
        expect(ret).toStrictEqual(plainToLdapStatus(newStatus));
        expect(mockAxios.get).toHaveBeenCalledWith(`/v1/ldap/status`);
        done();
      });
  });

  it('has ldap status fail handling', done => {
    store.state.adm!.ldapStatus = null;
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('adm/ldapStatus')
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has ldap ping', done => {
    store.state.adm!.ldapPingResponse = null;
    const pingResponse = makeTestPing();
    mockAxios.get.mockResolvedValue({ data: { data: pingResponse }});
    const promise = store.dispatch('adm/ldapPing');
    expect(store.state.adm!.status).toBe('loading');
    promise.then(res => { 
      expect(store.state.adm!.status).toBe('success');
      expect(mockAxios.get).toHaveBeenCalledWith(`/v1/ldap/ping`);
      expect(store.state.adm!.ldapPingResponse).toStrictEqual(plainToLdapPing(pingResponse));
      done();
    });
  });

  it('has ldap ping fail hanlding', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('adm/ldapPing')
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has get ldap sync adm key', done => {
    const testResponse = {
      key: 'ldap_sync_results',
      val: {
        job: 12,
        started: '2020-10-12',
        finished: '2020-10-13',
        synced: ['eins', 'zwei'],
        conflict: ['drei'],
        failed: ['vier', 'funf'],
        success: true,
        exception: undefined,
      },
    };
    const expectResponse = {
      job: 12,
      started: new Date('2020-10-12'),
      finished: new Date('2020-10-13'),
      synced: [ 'eins', 'zwei' ],
      conflict: [ 'drei' ],
      failed: [ 'vier', 'funf' ],
      success: true,
      exception: undefined,
    };

    mockAxios.get.mockResolvedValue({ data: { data: testResponse }});
    const promise = store.dispatch('adm/ldapSyncResults')
    expect(store.state.adm!.status).toBe('loading');
    promise.then(res => {

      expect(store.state.adm!.status).toBe('success');
      expect(store.state.adm!.ldapSyncResults).toStrictEqual(expectResponse);
      expect(mockAxios.get).toHaveBeenCalledWith(`/v1/adm/ldap_sync_results`)
      expect(res).toStrictEqual(expectResponse);
      done();
    });
  });
  it('has ldap sync results fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('adm/ldapSyncResults')
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('can trigger ldap sync', done => {
    const testJobResponse = {
      id: 'oink',
      status: 'running',
    };
    const testJobObj = plainToJob(testJobResponse);

    mockAxios.post.mockResolvedValue({ data: { data: testJobResponse }});
    const promise = store.dispatch('adm/syncLdap');
    expect(store.state.adm!.status).toBe('loading');
    promise.then(res => {
      expect(store.state.adm!.status).toBe('success');
      expect(mockAxios.post).toHaveBeenCalledWith(`/v1/ldap/sync`);
      expect(store.state.adm!.ldapSyncJob).toStrictEqual(testJobObj);
      expect(store.getters['adm/ldapSyncJob']).toStrictEqual(testJobObj);
      expect(res).toStrictEqual(testJobObj);
      done();
    });
  });
  it('has ldap sync fail handling', done => {
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('adm/syncLdap')
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has get ldap sync job info', done => {
    store.state.adm!.ldapSyncJob = plainToJob({ id: 'oink' });
    const testJobResponse = {
      id: 'oink',
      status: 'running',
    };
    const testJobObj = plainToJob(testJobResponse);

    mockAxios.get.mockResolvedValue({ data: { data: testJobResponse }});
    const promise = store.dispatch(`adm/syncLdapStatus`);
    expect(store.state.adm!.status).toBe('loading');
    promise.then(res => {
      expect(store.state.adm!.status).toBe('success');
      expect(mockAxios.get).toHaveBeenCalledWith(`/v1/jobs/oink`)
      expect(store.state.adm!.ldapSyncJob).toStrictEqual(testJobObj);
      expect(res).toStrictEqual(testJobObj);
      done();
    });
  });
  it('has get ldap sync job info with missing job', done => {
    store.state.adm!.ldapSyncJob = null;
    mockAxios.get.mockReset();
    const promise = store.dispatch(`adm/syncLdapStatus`);
    promise.then(res => {
      expect(store.state.adm!.status).toBe('success');
      expect(mockAxios.get).not.toHaveBeenCalled();
      expect(store.state.adm!.ldapSyncJob).toBeNull();
      done();
    });
  });
  it('has get ldap sync job fail handling', done => {
    store.state.adm!.ldapSyncJob = plainToJob({ id: 'oink' });
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch(`adm/syncLdapStatus`)
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has get job info action', done => {
    const testJobResponse = {
      id: 'oink',
      status: 'running',
    };
    const testJobObj = plainToJob(testJobResponse);

    mockAxios.get.mockResolvedValue({ data: { data: testJobResponse }});
    const promise = store.dispatch('adm/jobInfo', 'oink');
    expect(store.state.adm!.status).toBe('loading');
    promise.then(res => {
      expect(store.state.adm!.status).toBe('success');
      expect(mockAxios.get).toHaveBeenCalledWith(`/v1/jobs/oink`);
      expect(res).toStrictEqual(testJobObj);
      done();
    });
  });
  it('has get job fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('adm/jobInfo', 'oink')
      .catch(err => {
        expect(store.state.adm!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

});