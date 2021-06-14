import store from '@/store';

import { Manifest, plainToManifest, serializeManifest } from '@/store/models';

import { map as _map } from 'lodash';

import axios from 'axios';

jest.mock('axios')
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

export const testManifests = [
  { 'id': "1", containerName: 'oinktainer', createdAt: new Date(), content: { 'some': 'thing' } },
  { 'id': "2", containerName: 'oinktainer', createdAt: new Date(), content: { 'other': 'thing' } },
];
export const testManifestsObj = _map(testManifests, plainToManifest);

describe('manifest store getters', () => {
  it('has status getter', () => {
    store.state.manifests!.status = 'loading';
    expect(store.getters['manifests/status']).toBe('loading');
  });
  it('has list getter', () => {
    store.state.manifests!.list = testManifestsObj;
    expect(store.getters['manifests/list']).toStrictEqual(testManifestsObj)
  })
});

describe('mutations', () => {
  it('has status mutations', () => {
    store.state.manifests!.status = '';
    store.commit('manifests/loading');
    expect(store.state.manifests!.status).toBe('loading');
    store.commit('manifests/succeeded');
    expect(store.state.manifests!.status).toBe('success');
    store.commit('manifests/failed');
    expect(store.state.manifests!.status).toBe('failed');
  });

  it('has setList mutation', () => {
    store.state.manifests!.list = [];
    store.commit('manifests/setList', testManifestsObj);
    expect(store.state.manifests!.list).toStrictEqual(testManifestsObj);
  });

});

describe('actions', () => {
  it('has load list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testManifestsObj },
    });
    const promise = store.dispatch('manifests/list', { entityName: 'oinktity', collectionName: 'oinktion', containerName: 'oinktainer' });
    expect(store.state.manifests!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/containers/oinktity/oinktion/oinktainer/manifests`);
      expect(store.state.manifests!.status).toBe('success');
      expect(store.state.manifests!.list).toStrictEqual(testManifestsObj);
      done();
    });
  });
  it('has list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('manifests/list', { entityName: 'test', collectionName: 'test', containerName: 'test' })
      .catch(err => {
        expect(store.state.manifests!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });
});