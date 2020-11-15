import store from '@/store';
import { plainToUser, plainToUpload, } from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

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
});

describe('container store mutations', () => {
  it('has containers status mutations', () => {
    store.state.containers!.status = '';
    store.commit('containers/latestLoading');
    expect(store.state.containers!.status).toBe('loading');
    store.commit('containers/latestLoadingSucceeded', testLatest);
    expect(store.state.containers!.status).toBe('success');
    expect(store.state.containers!.latest).toStrictEqual(testLatestObj);
    store.commit('containers/latestLoadingFailed');
    expect(store.state.containers!.status).toBe('failed');
  });
});

describe('container store actions', () => {
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