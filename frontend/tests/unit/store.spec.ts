
import store from '@/store';
import { plainToUser, plainToUpload, plainToToken, serializeToken, Token } from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

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
      name: 'testhase', createdAt: new Date(),
    },
  },
  {
    tags: ['drei', 'vier'],
    container: {
      name: 'testnilpferd', createdAt: new Date(),
    },
  }
];
export const testLatestObj = _map(testLatest, plainToUpload);

const testTokens = [
  { id: '1', token: 'supersecret', createdAt: new Date(), comment: 'eins', },
  { id: '2', token: 'auchgeheim', createdAt: new Date(), comment: 'zwei', },
];
export const testTokenObj = _map(testTokens, plainToToken);


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
  });

  it('has tokens status getter', () => {
    store.state.tokens.status = 'loading';
    expect(store.getters['tokens/status']).toBe('loading');
  });
  it('has token list getter', () => {
    store.state.tokens.tokens = testTokenObj;
    expect(store.getters['tokens/tokens']).toStrictEqual(testTokenObj);
  });

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
});

describe('container store mutations', () => {
  it('has containers status mutations', () => {
    store.state.containers.status = '';
    store.commit('containers/latestLoading');
    expect(store.state.containers.status).toBe('loading');
    store.commit('containers/latestLoadingSucceeded', testLatest);
    expect(store.state.containers.status).toBe('success');
    expect(store.state.containers.latest).toStrictEqual(testLatestObj);
    store.commit('containers/latestLoadingFailed');
    expect(store.state.containers.status).toBe('failed');
  });
});

describe('token store mutations', () => {
  it('has token status mutations', () => {
    store.state.tokens.status = '';
    store.commit('tokens/tokensLoading');
    expect(store.state.tokens.status).toBe('loading');

    store.commit('tokens/tokensLoadingSucceeded', testTokens);
    expect(store.state.tokens.status).toBe('success');

    store.commit('tokens/tokensLoadingFailed');
    expect(store.state.tokens.status).toBe('failed');
  });

  it('has list update mutation', () => {
    store.state.tokens.tokens = [];
    store.commit('tokens/setList', testTokenObj);
    expect(store.state.tokens.tokens).toStrictEqual(testTokenObj);
  });

  it('has replace mutation', () => {
    store.state.tokens.tokens = _clone(testTokenObj);

    const updateToken = _clone(_find(testTokenObj, t => t.id === '1'));
    if (!updateToken) {
      throw 'updateToken not found';
    }
    updateToken.comment = 'changed me';

    store.commit('tokens/updateToken', updateToken);
    const updated = _find(store.state.tokens.tokens, t => t.id === updateToken.id);
    expect(updated).toStrictEqual(updateToken);
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
    expect(mockAxios.post).toHaveBeenLastCalledWith('/v1/get-token', postData);
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

  it('has logout action', done => {
    store.state.authStatus='success';
    store.dispatch('logout').then(() => {
      expect(store.state.authStatus).toBe('');
      done();
    });
  });
});

describe('container store actions', () => {
  it('has load latest containers', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testLatest },
    });
    const promise = store.dispatch('containers/latest');
    expect(mockAxios.get).toHaveBeenLastCalledWith('/v1/latest');
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

describe('token store actions', () => {
  it('has load token list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testTokens },
    });
    store.state.currentUser = testUserObj;
    const promise = store.dispatch('tokens/list');
    expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/tokens`);
    expect(store.state.tokens.status).toBe('loading');
    promise.then(() => {
      expect(store.state.tokens.status).toBe('success');
      expect(store.state.tokens.tokens).toStrictEqual(testTokenObj);
      done();
    });
  });
  it('has load token list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('tokens/list').catch(err => {
      expect(store.state.tokens.status).toBe('failed');
      done();
    });
  });

  it('has create token', done => {
    const createToken = {
      comment: 'comment me'
    };
    const createTokenObj = plainToToken(createToken);

    mockAxios.post.mockResolvedValue({
      data: { data: { id: "666", comment: createToken.comment }}
    });
    store.state.currentUser = testUserObj;

    const promise = store.dispatch('tokens/create', createTokenObj);
    expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/tokens`, serializeToken(createTokenObj));
    expect(store.state.tokens.status).toBe('loading');
    promise.then(() => {
      expect(store.state.tokens.status).toBe('success');
      const created = _find(store.state.tokens.tokens, t => t.id==="666");
      createTokenObj.id = created.id;
      expect(created).toStrictEqual(createTokenObj);
      done();
    });
  });
  it('has create token fail handling', done => {
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('tokens/create', testTokenObj[0]).catch(err => {
      expect(store.state.tokens.status).toBe('failed');
      done();
    });
  });

  it('has update token', done => {
    const updateToken = _clone(_find(testTokens, t => t.id==='1'));
    if (!updateToken) {
      throw 'test token not found';
    }
    updateToken.comment = 'oink';
    const updateTokenObj = plainToToken(updateToken);

    mockAxios.post.mockResolvedValue({
      data: { data: updateToken }
    });
    store.state.currentUser = testUserObj;
    store.state.tokens.tokens = _clone(testTokenObj);

    const promise = store.dispatch('tokens/update', updateTokenObj);
    expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/tokens/${updateToken.id}`, serializeToken(updateTokenObj));
    expect(store.state.tokens.status).toBe('loading');
    promise.then(() => {
      expect(store.state.tokens.status).toBe('success');
      expect(store.state.tokens.tokens).toHaveLength(2);
      const updated = _find(store.state.tokens.tokens, t => t.id===updateToken.id);
      expect(updated).toStrictEqual(updateTokenObj);
      done();
    });
  });
  it('has update token fail handling', done => {
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('tokens/update', testTokenObj[0]).catch(err => {
      expect(store.state.tokens.status).toBe('failed');
      done();
    });
  });

  it('has delete token', done => {
    store.state.currentUser = testUserObj;
    store.state.tokens.tokens = _clone(testTokenObj);

    mockAxios.delete.mockResolvedValue({
      data: { status: 'ok' },
    });
    const promise = store.dispatch('tokens/delete', testTokenObj[0].id);
    expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/tokens/${testTokenObj[0].id}`);
    expect(store.state.tokens.status).toBe('loading');
    promise.then(() => {
      expect(store.state.tokens.status).toBe('success');
      expect(store.state.tokens.tokens).toHaveLength(1);
      const deleted = _find(store.state.tokens.tokens, t => t.id === testTokenObj[0].id);
      expect(deleted).toBeUndefined();
      done();
    });
  });
  it('has delete token fail handling', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('tokens/delete', '1').catch(err => {
      expect(store.state.tokens.status).toBe('failed');
      done();
    });
  });

});