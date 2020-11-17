import store from '@/store';
import { plainToUser, plainToUpload, plainToContainer, } from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

export const testContainers = [
  { id: "1", name: "testhippo", description: 'Nilpferd', createdAt: new Date(), },
  { id: "2", name: "testzebra", description: 'Streifig', createdAt: new Date(), },
];
export const testContainersObj = _map(testContainers, plainToContainer);

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

describe('container store getters', () => {
  it('has containers status getter', () => {
    store.state.containers!.status = 'loading';
    expect(store.getters['containers/status']).toBe('loading');
  });

  it('has latest containers getter', () => {
    store.state.containers!.latest = testLatestObj;
    expect(store.getters['containers/latest']).toStrictEqual(testLatestObj);
  });

  it('has list getter', () => {
    store.state.containers!.list = testContainersObj;
    expect(store.getters['containers/list']).toStrictEqual(testContainersObj);
  });
});

describe('container store mutations', () => {
  it('has containers status mutations', () => {
    store.state.containers!.status = '';
    store.commit('containers/loading');
    expect(store.state.containers!.status).toBe('loading');
    store.commit('containers/succeeded', testLatest);
    expect(store.state.containers!.status).toBe('success');
    expect(store.state.containers!.latest).toStrictEqual(testLatestObj);
    store.commit('containers/failed');
    expect(store.state.containers!.status).toBe('failed');
  });
});

describe('container store actions', () => {
  it('has load container list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testContainersObj },
    });
    const promise = store.dispatch('containers/list', { entity: 'test', collection: 'hase' });
    expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/containers/test/hase`);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(() => {
      expect(store.state.containers!.status).toBe('success');
      expect(store.state.containers!.list).toStrictEqual(testContainersObj);
      done();
    });
  });
  it('has load container list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/list', { entity: 'test', collection: 'hase' }).catch(err => {
      expect(store.state.containers!.status).toBe('failed');
      done();
    });
  });

  it('has load latest containers', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testLatest },
    });
    const promise = store.dispatch('containers/latest');
    expect(mockAxios.get).toHaveBeenLastCalledWith('/v1/latest');
    expect(store.state.containers!.status).toBe('loading');
    promise.then(() => {
      expect(store.state.containers!.status).toBe('success');
      expect(store.state.containers!.latest).toStrictEqual(testLatestObj);
      done();
    });
  });

  it('has load latest containers fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/latest').catch(err => {
      expect(store.state.containers!.status).toBe('failed');
      done();
    });
  });
});