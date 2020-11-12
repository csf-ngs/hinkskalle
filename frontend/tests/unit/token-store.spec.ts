import store from '@/store';
import { plainToToken, serializeToken } from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import { testUserObj } from './store.spec';

store.state.backend = mockAxios;

const testTokens = [
  { id: '1', token: 'supersecret', createdAt: new Date(), comment: 'eins', },
  { id: '2', token: 'auchgeheim', createdAt: new Date(), comment: 'zwei', },
];
export const testTokenObj = _map(testTokens, plainToToken);

describe('token store getters', () => {
  it('has tokens status getter', () => {
    store.state.tokens.status = 'loading';
    expect(store.getters['tokens/status']).toBe('loading');
  });
  it('has token list getter', () => {
    store.state.tokens.tokens = _clone(testTokenObj);
    expect(store.getters['tokens/tokens']).toStrictEqual(testTokenObj);
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
    store.commit('tokens/setList', _clone(testTokenObj));
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

    mockAxios.put.mockResolvedValue({
      data: { data: updateToken }
    });
    store.state.currentUser = testUserObj;
    store.state.tokens.tokens = _clone(testTokenObj);

    const promise = store.dispatch('tokens/update', updateTokenObj);
    expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/tokens/${updateToken.id}`, serializeToken(updateTokenObj));
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
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
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