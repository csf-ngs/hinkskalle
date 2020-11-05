
import store from '@/store';
import { User } from '@/store';

import axios from 'axios';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

const testUser: User = {
      username: 'test.hase',
      email: 'test@ha.se',
      fullname: 'Test Hase',
      role: 'user',
      extra_data: {},
    };

describe('store getters', () => {
  it('has isLoggedIn getter', () => {
    expect(store.getters.isLoggedIn).toBe(false);
    store.state.currentUser = testUser;
    expect(store.getters.isLoggedIn).toBe(true);
  });
  it('has currentUser getter', () => {
    store.state.currentUser = testUser;
    expect(store.getters.currentUser).toBe(testUser);
  });
  it('has showSnackbar getter', () => {
    store.state.snackbar.show = false;
    expect(store.getters.showSnackbar).toBe(false);
    store.state.snackbar.show = true;
    expect(store.getters.showSnackbar).toBe(true);
  });
  it('has snackbarMsg getter', () => {
    store.state.snackbar.msg = 'oink';
    expect(store.getters.snackbarMsg).toBe('oink');
  });
});

describe('store mutations', () => {
  it('has snackbar mutations', () => {
    store.commit('openSnackbar', 'Oink!');
    expect(store.state.snackbar.msg).toBe('Oink!');
    expect(store.state.snackbar.show).toBe(true);

    store.commit('closeSnackbar');
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

    store.commit('authSuccess', { token: 'supersecret', user: testUser });
    expect(store.state.authStatus).toBe('success');
    expect(store.state.authToken).toBe('supersecret');
    expect(store.state.currentUser).toBe(testUser);
    expect(store.state.backend.defaults.headers.common['Authorization']).toBe(`Bearer supersecret`);
  });

  it('has authFailed mutation', () => {
    store.state.authStatus = '';
    store.state.currentUser = testUser;
    store.state.authToken = 'oink';
    store.state.backend.defaults.headers.common['Authorization']='oink';

    store.commit('authFailed', {});
    expect(store.state.authStatus).toBe('failed');
    expect(store.state.currentUser).toBeNull();
    expect(store.state.authToken).toBe('');
    expect(store.state.backend.defaults.headers.common).not.toHaveProperty('Authorization');
    
  });
});

describe('store actions', () => {
  it('has requestAuth', () => {
    mockAxios.post.mockResolvedValue({
      data: { 
        token: 'superoink',
        user: testUser,
      }
    });
    const postData = { username: 'test.hase', password: 'supersecret'};
    const promise = store.dispatch('requestAuth', postData);
    expect(mockAxios.post).toBeCalledWith('/api/v1/get-token', postData);
    expect(store.state.authStatus).toBe('loading');
    promise.then(() => {
      expect(store.state.authStatus).toBe('success');
      expect(store.state.authToken).toBe('superoink');
      expect(store.state.currentUser).toBe(testUser);
    });

  });

  it('has requestAuth fail handling', () => {
    const postData = { username: 'test.hase', password: 'supersecret'};
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('requestAuth', postData).catch(err => {
      expect(store.state.authStatus).toBe('failed');
      expect(store.state.currentUser).toBeNull();
    });
  });

});