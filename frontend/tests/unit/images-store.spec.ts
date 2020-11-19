import store from '@/store';
import {plainToImage} from '@/store/models';

import axios from 'axios';

import { map as _map } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

export const testImages = [
  { id: "1", hash: "eins", entityName: "oinktity", collectionName: "oinktion", containerName: "oinktainer", createdAt: new Date(), tags: [ "latest", "v3" ] },
  { id: "2", hash: "zwei", entityName: "oinktity", collectionName: "oinktion", containerName: "oinktainer", createdAt: new Date(), tags: [ "v2" ] },
];
const testImagesObj = _map(testImages, plainToImage);

describe('image store getters', () => {
  it('has status getter', () => {
    store.state.images!.status = 'loading';
    expect(store.getters['images/status']).toBe('loading');
  });
  it('has list getter', () => {
    store.state.images!.list = testImagesObj;
    expect(store.getters['images/list']).toStrictEqual(testImagesObj);
  });
});

describe('mutations', () => {
  it('has status mutations', () => {
    store.state.images!.status = '';
    store.commit('images/loading');
    expect(store.state.images!.status).toBe('loading');
    store.commit('images/succeeded');
    expect(store.state.images!.status).toBe('success');
    store.commit('images/failed');
    expect(store.state.images!.status).toBe('failed');
  });

  it('has setList mutation', () => {
    store.state.images!.list = [];
    store.commit('images/setList', testImagesObj);
    expect(store.state.images!.list).toStrictEqual(testImagesObj);
  });
});

describe('actions', () => {
  it('has load list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testImagesObj },
    });
    const promise = store.dispatch('images/list', { entityName: 'oinktity', collectionName: 'oinktion', containerName: 'oinktainer' });
    expect(store.state.images!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/containers/oinktity/oinktion/oinktainer/images`);
      expect(store.state.images!.status).toBe('success');
      expect(store.state.images!.list).toStrictEqual(testImagesObj);
      done();
    });
  });
  it('has list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('images/list', { entityName: 'test', collectionName: 'test', containerName: 'test' })
      .catch(err => {
        expect(store.state.images!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

});
