import store from '@/store';

import { makeTestSearchResult, makeTestSearchResultObj } from '../_data';

import axios from 'axios';
jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;
store.state.backend = mockAxios;

describe('search store getters', () => {
  it('has status getter', () => {
    store.state.search!.status = 'loading';
    expect(store.getters['search/status']).toBe('loading');
  });
  it('has results getter', () => {
    const testResult = makeTestSearchResultObj();
    store.state.search!.results = testResult;
    expect(store.getters['search/results']).toStrictEqual(testResult);
  })

});

describe('search store actions', () => {
  it('has search', done => {
    const testResult = makeTestSearchResult();
    const testResultObj = makeTestSearchResultObj(testResult);
    mockAxios.get.mockResolvedValue({ 
      data: { data: testResult }
    });

    const promise = store.dispatch('search/any', { name: 'test', description: 'hase' });
    expect(store.state.search!.status).toBe('loading');
    promise.then(res => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/search`, { params: { value:'test', description:'hase' }});
      expect(store.state.search!.status).toBe('success');
      expect(store.state.search!.results).toStrictEqual(testResultObj);
      expect(res).toStrictEqual(testResultObj);
      done();
    });
  });
  it('has search fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('search/any', { name: 'test' })
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

});