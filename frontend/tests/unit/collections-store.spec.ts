import store from '@/store';
import {Collection, plainToCollection, serializeCollection, Entity} from '@/store/models';
import { map as _map, clone as _clone, concat as _concat, find as _find } from 'lodash';

import axios from 'axios';
jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import entitiesModule from '@/store/modules/entities';
jest.mock('@/store/modules/entities');
const mockEntities = entitiesModule as jest.Mocked<typeof entitiesModule>;

import { testUser, testUserObj } from './store.spec';
import collectionsModule from '@/store/modules/collections';

store.state.backend = mockAxios;

const testCollections = [
  {
    id: '1', name: 'esel', description: 'eyore', createdAt: new Date(), entityName: 'oinktity',
  },
  {
    id: '2', name: 'schaf', description: 'shawn', createdAt: new Date(), entityName: 'wooftity',
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

  it('has remove mutation', () => {
    const toRemove = testCollectionsObj[0];
    store.state.collections!.list = _clone(testCollectionsObj);
    store.commit('collections/remove', toRemove.id);
    expect(store.state.collections!.list).toHaveLength(1);
    const removed = _find(store.state.collections!.list, c => c.id === toRemove.id);
    expect(removed).toBeUndefined();
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

  it('has create collection with known entity id', done => {
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

  it('has create collection with known entity name', done => {
    const collection = {
      name: "testilein",
      entityName: "oinktity"
    };
    const createCollectionObj = plainToCollection(collection);

    const fakeEntity = new Entity();
    fakeEntity.id = "877";
    fakeEntity.name = "oinktity";

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', entity: fakeEntity.id, entityName: fakeEntity.name, name: collection.name }}
    });
    (mockEntities as any).actions.get.mockResolvedValue(fakeEntity);
    const promise = store.dispatch('collections/create', createCollectionObj);
    expect(store.state.collections!.status).toBe('loading');
    promise.then(collection => {
      expect(mockEntities!.actions!.get).toHaveBeenLastCalledWith(expect.anything(), "oinktity");
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

  it('has create collection with default/user entity', done => {
    const collection = {
      name: "testilein",
    };
    const createCollectionObj = plainToCollection(collection);
    store.state.currentUser = testUserObj;

    const fakeEntity = new Entity();
    fakeEntity.id = "977";
    fakeEntity.name = testUserObj.username;

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', entity: fakeEntity.id, entityName: fakeEntity.name, name: collection.name }}
    });
    (mockEntities as any).actions.get.mockResolvedValue(fakeEntity);
    const promise = store.dispatch('collections/create', createCollectionObj);
    expect(store.state.collections!.status).toBe('loading');
    promise.then(collection => {
      expect(mockEntities!.actions!.get).toHaveBeenLastCalledWith(expect.anything(), testUserObj.username);
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


  it('has create collection/get entity failed fallback', done => {
    (mockEntities as any).actions.get.mockRejectedValue({ fail: 'fail' });
    const collection = {
      name: "testilein",
      entityName: "oinktity"
    };
    const createCollectionObj = plainToCollection(collection);
    store.dispatch('collections/create', createCollectionObj)
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.collections!.status).toBe('failed');
        done();
      });
  });

  it('has create collection fail handling', done => {
    const collection = {
      name: "testilein",
      entity: 999,
    };
    const createCollectionObj = plainToCollection(collection);
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('collections/create', createCollectionObj)
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.collections!.status).toBe('failed');
        done();
      });
  });

  it('has update', done => {
    const update = _clone(_find(testCollections, c => c.id==="1"));
    if (!update) {
      throw 'test collection not found';
    }
    update.description = 'tohuwabohu';
    const updateObj = plainToCollection(update);

    mockAxios.put.mockResolvedValue({
      data: { data: update } 
    });

    store.state.collections!.list = _clone(testCollectionsObj);

    const promise = store.dispatch('collections/update', updateObj);
    expect(store.state.collections!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/collections/${updateObj.entityName}/${updateObj.name}`, serializeCollection(updateObj));
      expect(store.state.collections!.status).toBe('success');
      expect(store.state.collections!.list).toHaveLength(2);
      const updated = _find(store.state.collections!.list, c => c.id===update.id);
      expect(updated).toStrictEqual(updateObj);
      done();
    });
  });
  it('has update fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('collections/update', testCollectionsObj[0]).catch(err => {
      expect(store.state.collections!.status).toBe('failed');
      expect(err).toStrictEqual({ fail: 'fail' });
      done();
    });
  });

  it('has delete', done => {
    store.state.collections!.list = _clone(testCollectionsObj);
    mockAxios.delete.mockResolvedValue({
      data: { status: 'ok' },
    });
    const promise = store.dispatch('collections/delete', testCollectionsObj[0]);
    expect(store.state.collections!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/collections/${testCollectionsObj[0].entityName}/${testCollectionsObj[0].name}`)
      expect(store.state.collections!.status).toBe('success');
      expect(store.state.collections!.list).toHaveLength(1);
      const deleted = _find(store.state.collections!.list, c => c.id === testCollectionsObj[0].id);
      expect(deleted).toBeUndefined();
      done();
    });
  });
  it('has delete fail', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch(`collections/delete`, testCollectionsObj[0])
      .catch(err => {
        expect(store.state.collections!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  })

});