import store from '@/store';
import {plainToCollection} from '@/store/models';

import axios from 'axios';

import { map as _map } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import { testUser, testUserObj } from './store.spec';

store.state.backend = mockAxios;

const testCollections = [
  {
    name: 'esel', 
  },
  {
    name: 'schaf',
  }
];

export const testCollectionsObj = _map(testCollections, plainToCollection);

describe('collection store getters', () => {
  it('has collections status getter', () => {
    store.state.collections.status = 'loading';
    expect(store.getters['collections/status']).toBe('loading');
  });

  it('has collection list getter', () => {
    store.state.collections.list = testCollectionsObj;
    expect(store.getters['collections/list']).toStrictEqual(testCollectionsObj);
  });
});

describe('collection store mutations', () => {
  it('has status mutations', () => {
    store.state.collections.status = '';
    store.commit('collections/loading');
    expect(store.state.collections.status).toBe('loading');
    store.commit('collections/succeeded');
    expect(store.state.collections.status).toBe('success');
    store.commit('collections/failed');
    expect(store.state.collections.status).toBe('failed');
  });

  it('has setList mutation', () => {
    store.state.collections.list = [];
    store.commit('collections/setList', testCollectionsObj);
    expect(store.state.collections.list).toStrictEqual(testCollectionsObj);
  });

});

describe('collection store actions', () => {
  it('has load collection list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testCollections },
    });
    store.state.currentUser = testUserObj;
    const promise = store.dispatch('collections/list');
    expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/collections/${testUserObj.username}`);
    expect(store.state.collections.status).toBe('loading');
    promise.then(() => {
      expect(store.state.collections.status).toBe('success');
      expect(store.state.collections.list).toStrictEqual(testCollectionsObj);
      done();
    });
  });
  it('has load collection list for other entity', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testCollections },
    });
    store.state.currentUser = testUserObj;
    const promise = store.dispatch('collections/list', 'oi.nk');
    expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/collections/oi.nk`);
    expect(store.state.collections.status).toBe('loading');
    promise.then(() => {
      expect(store.state.collections.status).toBe('success');
      expect(store.state.collections.list).toStrictEqual(testCollectionsObj);
      done();
    });
  });
  it('has load collection list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('collections/list').catch(err => {
      expect(err).toStrictEqual({ fail: 'fail' });
      expect(store.state.collections.status).toBe('failed');
      done();
    });
  });

});