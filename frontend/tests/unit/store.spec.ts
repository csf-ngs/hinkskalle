
import store from '@/store';
import { plainToUser, plainToUpload } from '@/store/models';

import axios from 'axios';

import { map as _map } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

const testUser = {
      username: 'test.hase',
      email: 'test@ha.se',
      firstname: 'Test',
      lastname: 'Hase',
      isAdmin: false,
    };
  
const testUserObj = plainToUser(testUser);

const testLatest = [
  { 
    tags: ['eins', 'zwei'], 
    container: {
      name: 'testhase',
    },
  },
  {
    tags: ['drei', 'vier'],
    container: {
      name: 'testnilpferd',
    },
  }
]

export const testLatestObj = _map(testLatest, plainToUpload);

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
  
  it('has showSnackbar getter', () => {
    store.state.snackbar.show = false;
    expect(store.getters['snackbar/show']).toBe(false);
    store.state.snackbar.show = true;
    expect(store.getters['snackbar/show']).toBe(true);
  });
  it('has snackbarMsg getter', () => {
    store.state.snackbar.msg = 'oink';
    expect(store.getters['snackbar/msg']).toBe('oink');
  });

  it('has containers status getter', () => {
    store.state.containers.status = 'loading';
    expect(store.getters['containers/status']).toBe('loading');
  });

  it('has latest containers getter', () => {
    store.state.containers.latest = testLatestObj;
    expect(store.getters['containers/latest']).toStrictEqual(testLatestObj);
  })
});

describe('store mutations', () => {
  it('has snackbar mutations', () => {
    store.commit('snackbar/open', 'Oink!');
    expect(store.state.snackbar.msg).toBe('Oink!');
    expect(store.state.snackbar.show).toBe(true);

    store.commit('snackbar/close');
    expect(store.state.snackbar.msg).toBe('');
    expect(store.state.snackbar.show).toBe(false);
  });

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

  it('has containers status mutation', () => {
    store.state.containers.status = '';
    store.commit('containers/latestLoading');
    expect(store.state.containers.status).toBe('loading');
    store.commit('containers/latestLoadingSucceeded');
    expect(store.state.containers.status).toBe('success');
    store.commit('containers/latestLoadingFailed');
    expect(store.state.containers.status).toBe('failed');

  });
});

describe('store actions', () => {
  it('has requestAuth', done => {
    mockAxios.post.mockResolvedValue({
      data: { 
        data: {
          token: 'superoink',
          user: testUser,
        },
      }
    });
    const postData = { username: 'test.hase', password: 'supersecret'};
    const promise = store.dispatch('requestAuth', postData);
    expect(mockAxios.post).toBeCalledWith('/v1/get-token', postData);
    expect(store.state.authStatus).toBe('loading');
    promise.then(() => {
      expect(store.state.authStatus).toBe('success');
      expect(store.state.authToken).toBe('superoink');
      expect(store.state.currentUser).toStrictEqual(testUserObj);
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

  it('has load latest containers', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testLatest },
    });
    const promise = store.dispatch('containers/latest');
    expect(mockAxios.get).toHaveBeenCalledWith('/v1/latest');
    expect(store.state.containers.status).toBe('loading');
    promise.then(() => {
      expect(store.state.containers.status).toBe('success');
      expect(store.state.containers.latest).toStrictEqual(testLatestObj);
      done();
    });
  });

  it('has load latest containers fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/latest').catch(err => {
      expect(store.state.containers.status).toBe('failed');
      done();
    });
  });

});