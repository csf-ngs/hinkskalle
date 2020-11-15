import store from '@/store';
import {Collection, plainToCollection, serializeCollection} from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, concat as _concat, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import { testUser, testUserObj } from './store.spec';

store.state.backend = mockAxios;

const testCollections = [
  {
    id: '1', name: 'esel', description: 'eyore', createdAt: new Date(),
  },
  {
    id: '2', name: 'schaf', description: 'shawn', createdAt: new Date(),
  }
];

export const testCollectionsObj = _map(testCollections, plainToCollection);

describe('collection store getters', () => {
  it('has collections status getter', () => {
    store.state.collections!.status = 'loading';
    expect(store.getters['collections/status']).toBe('loading');
  });

  it('has collection list getter', () => {
    store.state.collections!.list = testCollectionsObj;
    expect(store.getters['collections/list']).toStrictEqual(testCollectionsObj);
  });
});

describe('collection store mutations', () => {
  it('has status mutations', () => {
    store.state.collections!.status = '';
    store.commit('collections/loading');
    expect(store.state.collections!.status).toBe('loading');
    store.commit('collections/succeeded');
    expect(store.state.collections!.status).toBe('success');
    store.commit('collections/failed');
    expect(store.state.collections!.status).toBe('failed');
  });

  it('has setList mutation', () => {
    store.state.collections!.list = [];
    store.commit('collections/setList', testCollectionsObj);
    expect(store.state.collections!.list).toStrictEqual(testCollectionsObj);
  });

  it('has update mutation', () => {
    store.state.collections!.list = _clone(testCollectionsObj);
    const update = _clone(_find(testCollectionsObj, c => c.id === '1'));
    if (!update) {
      throw 'update collection test not found';
    }
    update.description = 'Woof';
    store.commit('collections/update', update);

    const updated = _find(store.state.collections!.list, c => c.id === update.id);
    expect(updated).toStrictEqual(update);
    expect(store.state.collections!.list).toHaveLength(2);

    const create = new Collection();
    create.id="999";
    create.name="supercow";
    create.createdAt = new Date();

    store.commit('collections/update', create);
    expect(store.state.collections!.list).toHaveLength(3);
    const added = _find(store.state.collections!.list, c => c.id === create.id);
    expect(added).toStrictEqual(create);
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
    expect(store.state.collections!.status).toBe('loading');
    promise.then(() => {
      expect(store.state.collections!.status).toBe('success');
      expect(store.state.collections!.list).toStrictEqual(testCollectionsObj);
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
    expect(store.state.collections!.status).toBe('loading');
    promise.then(() => {
      expect(store.state.collections!.status).toBe('success');
      expect(store.state.collections!.list).toStrictEqual(testCollectionsObj);
      done();
    });
  });
  it('has load collection list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.state.currentUser = testUserObj;
    store.dispatch('collections/list').catch(err => {
      expect(err).toStrictEqual({ fail: 'fail' });
      expect(store.state.collections!.status).toBe('failed');
      done();
    });
  });

  it('has create collection', done => {
    const collection = {
      name: 'testilein',
      entity: "777",
    };
    const createCollectionObj = plainToCollection(collection);

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', entity: "777", name: collection.name }}
    });
    store.state.currentUser = testUserObj;

    const promise = store.dispatch('collections/create', createCollectionObj);
    expect(store.state.collections!.status).toBe('loading');
    promise.then(collection => {
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/collections`, serializeCollection(createCollectionObj));
      expect(store.state.collections!.status).toBe('success');
      const created = _find(store.state.collections!.list, c => c.id==='666');
      if (!created) {
        throw Error('created id 666 not found in test token store');
      }
      createCollectionObj.id = created.id;
      expect(created).toStrictEqual(createCollectionObj);
      expect(collection).toStrictEqual(createCollectionObj);
      done();
    });
  });

});