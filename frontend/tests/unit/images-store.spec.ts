import store from '@/store';
import {Image, plainToImage, serializeImage} from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

export const testImages = [
  { id: "1", description: "oans", hash: "eins", entityName: "oinktity", collectionName: "oinktion", containerName: "oinktainer", createdAt: new Date(), tags: [ "latest", "v3" ] },
  { id: "2", description: "zwoa", hash: "zwei", entityName: "oinktity", collectionName: "oinktion", containerName: "oinktainer", createdAt: new Date(), tags: [ "v2" ] },
];
export const testImagesObj = _map(testImages, plainToImage);

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

  it('has update mutation', () => {
    store.state.images!.list = testImagesObj;
    const upd = _clone(testImagesObj[0]);
    upd.description = 'goat cheese with walnuts';
    store.commit('images/update', upd);
    expect(store.state.images!.list).toHaveLength(2);
    const found = _find(store.state.images!.list, i => i.id === upd.id);
    if (!found) {
      throw new Error('image not in list');
    }
    expect(found.description).toBe(upd.description);

    const newImg = new Image();
    newImg.id="donkey";
    newImg.description="grey";
    store.commit('images/update', newImg);
    expect(store.state.images!.list).toHaveLength(3);
    const newFound = _find(store.state.images!.list, i => i.id === newImg.id);
    if (!newFound) {
      throw new Error('New image not in list');
    }
    expect(newFound.description).toBe(newImg.description);
  });

  it('has remove mutation', () => {
    store.state.images!.list = testImagesObj;
    store.commit('images/remove', testImagesObj[0]);
    expect(store.state.images!.list).toHaveLength(1);
    const removed = _find(store.state.images!.list, i => i.id === testImagesObj[0].id);
    expect(removed).toBeUndefined();
  })

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

  it('has inspect', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: { attributes: { deffile: 'testhase' } } }
    });
    const promise = store.dispatch('images/inspect', testImagesObj[0]);
    expect(store.state.images!.status).toBe('loading');
    promise.then(attributes => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/images/${testImagesObj[0].fullPath}/inspect`);
      expect(store.state.images!.status).toBe('success');
      expect(attributes).toStrictEqual({ deffile: 'testhase' });
      done();
    });
  });
  it('has inspect fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('images/inspect', testImagesObj[0])
      .catch(err => {
        expect(store.state.images!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has update', done => {
    const update = _clone(_find(testImages, i => i.id==="1"));
    if (!update) {
      throw 'test image not found';
    }
    update.description="greeen donkey";
    const updateObj = plainToImage(update);
    mockAxios.put.mockResolvedValue({
      data: { data: update }
    });

    store.state.images!.list = _clone(testImagesObj);

    const promise = store.dispatch('images/update', updateObj);
    expect(store.state.images!.status).toBe('loading');
    promise.then(upd => {
      expect(mockAxios.put).toHaveBeenCalledWith(`/v1/images/${updateObj.entityName}/${updateObj.collectionName}/${updateObj.containerName}:${updateObj.hash}`, updateObj);
      expect(store.state.images!.status).toBe('success');
      expect(store.state.images!.list).toHaveLength(2);

      const updated = _find(store.state.images!.list, i => i.id===update.id);
      expect(updated).toStrictEqual(updateObj);
      expect(upd).toStrictEqual(updated);
      done();
    });
  });
  it('has update fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('images/update', testImagesObj[0])
      .catch(err => {
        expect(store.state.images!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has update tags', done => {
    const upd = _clone(testImagesObj[0]);
    upd.tags = [ 'v1' ];
    mockAxios.put.mockResolvedValue({ 
      data: { data: { tags: [ 'v1' ] }}
    });
    const promise = store.dispatch('images/updateTags', upd);
    expect(store.state.images!.status).toBe('loading');
    promise.then(tags => {
      expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/images/${upd.fullPath}/tags`, { tags: [ "v1" ] });
      expect(tags).toStrictEqual(["v1"]);
      expect(store.state.images!.status).toBe('success');
      const fromStore = _find(store.state.images!.list, i => i.id === upd.id);
      if (!fromStore) {
        throw new Error(`${upd.id} not found in store`);
      }
      expect(fromStore.tags).toStrictEqual(['v1']);
      done();
    });
  });
  it('has update tags fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('images/updateTags', testImagesObj[0])
      .catch(err => {
        expect(store.state.images!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has delete', done => {
    store.state.images!.list = _clone(testImagesObj);
    mockAxios.delete.mockResolvedValue({
      data: { status: 'ok' }
    });
    const promise = store.dispatch('images/delete', testImagesObj[0]);
    expect(store.state.images!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/images/${testImagesObj[0].entityName}/${testImagesObj[0].collectionName}/${testImagesObj[0].containerName}:${testImagesObj[0].hash}`);
      expect(store.state.images!.status).toBe('success');
      expect(store.state.images!.list).toHaveLength(1);
      const deleted = _find(store.state.images!.list, i => i.id === testImagesObj[0].id);
      expect(deleted).toBeUndefined();
      done();
    });
  });
  it('has delete fail', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch('images/delete', testImagesObj[0])
      .catch(err => {
        expect(store.state.images!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      })

  });

});
