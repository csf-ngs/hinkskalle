
import store from '@/store';

import { makeTestUser, makeTestUserObj } from '../_data';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';
import {plainToConfigParams, User} from '@/store/models';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;
store.state.backend = mockAxios;

let testUserObj: User;

beforeAll(() => {
  testUserObj = makeTestUserObj();
});

describe('store getters', () => {

  it('has isLoggedIn getter', () => {
    expect(store.getters.isLoggedIn).toBe(false);
    store.state.currentUser = testUserObj;
    expect(store.getters.isLoggedIn).toBe(true);
  });
  it('has currentUser getter', () => {
    store.state.currentUser = testUserObj;
    expect(store.getters.currentUser).toStrictEqual(testUserObj);

    expect(store.getters.currentUser.fullname).toBe('Test Hase');
    expect(store.getters.currentUser.role).toBe('user');
  });
  it('has config getter', () => {
    store.state.config = plainToConfigParams({
      default_user_quota: 0,
      enable_register: false,
      singularity_flavor: 'apptainer',
      frontend_url: 'http://localhost:7660',
    })

    expect(store.getters.config.default_user_quota).toBe(0);
    expect(store.getters.config.enable_register).toBe(false);
    expect(store.getters.config.singularity_flavor).toBe('apptainer');
    expect(store.getters.config.frontend_url).toBe('http://localhost:7660');
  });
  
});

describe('store mutations', () => {
  it('has authRequested mutation', () => {
    store.state.authStatus='';
    store.commit('authRequested');
    expect(store.state.authStatus).toBe('loading');
  });

  it('has authSuccess mutation', () => {
    store.state.authToken = '';
    store.state.authStatus = '';
    store.state.currentUser = null;

    store.commit('authSuccess', { token: 'supersecret', user: testUserObj });
    expect(store.state.authStatus).toBe('success');
    expect(store.state.authToken).toBe('supersecret');
    expect(store.state.currentUser).toStrictEqual(testUserObj);
    expect(store.state.currentUser!.fullname).toBe('Test Hase');
    expect(store.state.currentUser!.role).toBe('user');
    expect(store.state.backend.defaults.headers.common['Authorization']).toBe(`Bearer supersecret`);
  });

  it('has authFailed mutation', () => {
    store.state.authStatus = '';
    store.state.currentUser = testUserObj;
    store.state.authToken = 'oink';
    store.state.backend.defaults.headers.common['Authorization']='oink';

    store.commit('authFailed', {});
    expect(store.state.authStatus).toBe('failed');
    expect(store.state.currentUser).toBeNull();
    expect(store.state.authToken).toBe('');
    expect(store.state.backend.defaults.headers.common).not.toHaveProperty('Authorization');
    
  });

  it('has logout mutation', () => {
    store.state.authStatus = 'success';
    store.state.currentUser = testUserObj;
    store.state.authToken = 'oink';
    store.state.backend.defaults.headers.common['Authorization']='oink';

    store.commit('logout');
    expect(store.state.authStatus).toBe('');
    expect(store.state.currentUser).toBeNull();
    expect(store.state.authToken).toBe('');
    expect(store.state.backend.defaults.headers.common).not.toHaveProperty('Authorization');
  });

  it('has setConfig mutation', () => {
    store.state.config = null;
    const testConfig = plainToConfigParams({
      enable_register: false,
      default_user_quota: 999,
      singularity_flavor: 'apptainer',
      frontend_url: 'http://localhost:7660',
    });

    store.commit('setConfig', testConfig);
    expect(store.state.config).not.toBeNull();
    expect(store.state.config!.default_user_quota).toBe(999);
  });
});

describe('store actions', () => {
  const testUser = makeTestUser();
  it('has getConfig', done => {
    store.state.config = null;
    mockAxios.get.mockResolvedValue({
      data: {
        params: {
          default_user_quota: 999,
          enable_register: false,
          singularity_flavor: 'apptainer',
          frontend_url: 'http://localhost:7660',
        },
      }
    });
    const promise = store.dispatch('getConfig');
    expect(mockAxios.get).toHaveBeenLastCalledWith('/assets/config/config.prod.json');
    promise.then(() => {
      expect(store.state.config).not.toBe(null);
      expect(store.state.config!.default_user_quota).toBe(999);
      expect(store.state.config?.frontend_url).toBe('http://localhost:7660')
      done();
    });
  });
  it('has requestAuth', done => {
    mockAxios.post.mockResolvedValue({
      data: { 
        data: {
          generatedToken: 'superoink',
          user: testUser,
        },
      }
    });
    const postData = { username: 'test.hase', password: 'supersecret'};
    const promise = store.dispatch('requestAuth', postData);
    expect(mockAxios.post).toHaveBeenLastCalledWith('/v1/get-token', postData);
    expect(store.state.authStatus).toBe('loading');
    promise.then(() => {
      expect(store.state.authStatus).toBe('success');
      expect(store.state.authToken).toBe('superoink');
      expect(store.state.currentUser).toStrictEqual(makeTestUserObj(testUser));
      done();
    });

  });

  it('has requestAuth fail handling', done => {
    const postData = { username: 'test.hase', password: 'supersecret'};
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('requestAuth', postData).catch(err => {
      expect(store.state.authStatus).toBe('failed');
      expect(store.state.currentUser).toBeNull();
      done();
    });
  });

  it('has logout action', done => {
    store.state.authStatus='success';
    store.dispatch('logout').then(() => {
      expect(store.state.authStatus).toBe('');
      done();
    });
  });

  it('has getAuthnCreateOptions action', done => {
    mockAxios.get.mockResolvedValue({
      data: {
        "data": authnCreateOptions(),
      }
    });
    const promise = store.dispatch('getAuthnCreateOptions');
    promise.then((config: CredentialCreationOptions) => {
      expect(config.publicKey?.user.id).toBeInstanceOf(Uint8Array);
      expect(config.publicKey?.challenge).toBeInstanceOf(Uint8Array);
      done();

    });
  })
});

function authnCreateOptions() {
  return {
          "publicKey": {
            "authenticatorSelection": {
              "authenticatorAttachment":"cross-platform",
              "requireResidentKey":false,
              "userVerification":"discouraged"
            },
            "challenge":"AA==",
            "excludeCredentials":[],
            "pubKeyCredParams": [
              {"alg":-7,"type":"public-key"},
              {"alg":-257,"type":"public-key"}
            ],
            "rp":{
              "id":"localhost",
              "name":"Hinkskalle"
            },
            "timeout":180000,
            "user": {
              "displayName":"Test Hase",
              "id":"T90IiRrV940+Hed8BFHP+Q==",
              "name":"test.hase"
            }
          }
        };
}
