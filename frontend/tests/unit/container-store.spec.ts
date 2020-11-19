import store from '@/store';
import { plainToUpload, plainToContainer, serializeContainer, Entity, Collection, Container, } from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import collectionsModule from '@/store/modules/collections';
jest.mock('@/store/modules/collections');
const mockCollections = collectionsModule as jest.Mocked<typeof collectionsModule>;

store.state.backend = mockAxios;

export const testContainers = [
  { id: "1", name: "testhippo", collectionName: "oinktion", entityName: "oinktity", description: 'Nilpferd', createdAt: new Date(), },
  { id: "2", name: "testzebra", collectionName: "muhtion", entityName: "muhtity", description: 'Streifig', createdAt: new Date(), },
];
export const testContainersObj = _map(testContainers, plainToContainer);

const testLatest = [
  { 
    tags: ['eins', 'zwei'], 
    container: {
      name: 'testhase', createdAt: new Date(), collectionName: 'oinkton', entityName: 'oinktity',
    },
  },
  {
    tags: ['drei', 'vier'],
    container: {
      name: 'testnilpferd', createdAt: new Date(), collectionName: 'muhton', entityName: 'muhtity',
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
    store.commit('containers/succeeded');
    expect(store.state.containers!.status).toBe('success');
    store.commit('containers/failed');
    expect(store.state.containers!.status).toBe('failed');
  });

  it('has update mutation', () => {
    store.state.containers!.list = _clone(testContainersObj);
    const update = _clone(_find(testContainersObj, c => c.id === '1'));
    if (!update) {
      throw 'update test not found';
    }
    update.description = 'Woof';
    store.commit('containers/update', update);

    const updated = _find(store.state.containers!.list, c => c.id === update.id);
    expect(updated).toStrictEqual(update);
    expect(store.state.containers!.list).toHaveLength(2);

    const create = new Container();
    create.id="999";
    create.name="supercow";
    create.createdAt = new Date();

    store.commit('containers/update', create);
    expect(store.state.containers!.list).toHaveLength(3);
    const added = _find(store.state.containers!.list, c => c.id === create.id);
    expect(added).toStrictEqual(create);
  });

  it('has remove mutation', () => {
    const toRemove = testContainersObj[0];
    store.state.containers!.list = _clone(testContainersObj);
    store.commit('containers/remove', toRemove.id);
    expect(store.state.containers!.list).toHaveLength(1);
    const removed = _find(store.state.containers!.list, c => c.id === toRemove.id);
    expect(removed).toBeUndefined();
  });
});

describe('container store actions', () => {
  it('has load container list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testContainersObj },
    });
    const promise = store.dispatch('containers/list', { entityName: 'test', collectionName: 'hase' });
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
    store.dispatch('containers/list', { entityName: 'test', collectionName: 'hase' }).catch(err => {
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

  it('has get container', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testContainers[0] },
    });

    const promise = store.dispatch('containers/get', testContainersObj[0]);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(container => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/containers/${testContainers[0].entityName}/${testContainers[0].collectionName}/${testContainers[0].name}`);
      expect(store.state.containers!.status).toBe('success');
      expect(container).toStrictEqual(testContainersObj[0]);
      done();
    });
  });
  it('has get container fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/get', testContainersObj[0])
      .catch(err => {
        expect(store.state.containers!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has create container with known collection id', done => {
    const container = {
      name: 'testilein',
      collection: "1234",
    };
    const createContainerObj = plainToContainer(container);

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', collection: "1234", name: container.name }}
    });

    const promise = store.dispatch('containers/create', createContainerObj);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(container => {
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/containers`, serializeContainer(createContainerObj));
      expect(store.state.containers!.status).toBe('success');
      const created = _find(store.state.containers!.list, c => c.id==='666');
      if (!created) {
        throw Error('created id 666 not found in test store');
      }
      createContainerObj.id = created.id;
      expect(created).toStrictEqual(createContainerObj);
      expect(container).toStrictEqual(createContainerObj);
      done();
    });
  });

  it('has create container with entity/collection name', done => {
    const container = {
      name: 'testilein',
      entityName: 'oinktity',
      collectionName: 'oinktion',
    };
    const createContainerObj = plainToContainer(container);

    const fakeEntity = new Entity();
    fakeEntity.id = "111";
    fakeEntity.name = "oinktity";
    const fakeCollection = new Collection();
    fakeCollection.name = "oinktion";
    fakeCollection.id = "222";

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', entity: fakeEntity.id, entityName: fakeEntity.name, collection: fakeCollection.id, collectionName: fakeCollection.name, name: container.name }}
    });
    (mockCollections as any).actions.get.mockResolvedValue(fakeCollection);
    const promise = store.dispatch('containers/create', createContainerObj);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(container => {
      expect(mockCollections!.actions!.get).toHaveBeenLastCalledWith(expect.anything(), expect.objectContaining({ entityName: "oinktity", collectionName: "oinktion" }));
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/containers`, serializeContainer(createContainerObj));
      expect(store.state.containers!.status).toBe('success');
      const created = _find(store.state.containers!.list, c => c.id==='666');
      if (!created) {
        throw Error('created id 666 not found in test store');
      }
      createContainerObj.id = created.id;
      createContainerObj.entity = fakeEntity.id;
      expect(created).toStrictEqual(createContainerObj);
      expect(container).toStrictEqual(createContainerObj);
      done();
    });

  });

  it('has create container/get collection failed fallback', done => {
    (mockCollections as any).actions.get.mockRejectedValue({ fail: 'fail' });
    const container = {
      name: 'testilein',
      entityName: 'oinktity',
      collectionName: 'oinktion',
    };
    const createContainerObj = plainToContainer(container);
    store.dispatch('containers/create', createContainerObj)
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.containers!.status).toBe('failed');
        done();
      });
  });

  it('has create container failed fallback', done => {
    const container = {
      name: 'testilein',
      entityName: 'oinktity',
      collectionName: 'oinktion',
    };
    const createContainerObj = plainToContainer(container);
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/create', createContainerObj)
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.containers!.status).toBe('failed');
        done();
      });
  });

  it('has update', done => {
    const update = _clone(_find(testContainers, c => c.id==="1"));
    if (!update) {
      throw 'test container not found';
    }
    update.description = 'tohuwabohu';
    const updateObj = plainToContainer(update);

    mockAxios.put.mockResolvedValue({
      data: { data: update } 
    });

    store.state.containers!.list = _clone(testContainersObj);

    const promise = store.dispatch('containers/update', updateObj);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/containers/${updateObj.entityName}/${updateObj.collectionName}/${updateObj.name}`, serializeContainer(updateObj));
      expect(store.state.containers!.status).toBe('success');
      expect(store.state.containers!.list).toHaveLength(2);
      const updated = _find(store.state.containers!.list, c => c.id===update.id);
      expect(updated).toStrictEqual(updateObj);
      done();
    });
  });
  it('has update fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('containers/update', testContainersObj[0]).catch(err => {
      expect(store.state.containers!.status).toBe('failed');
      expect(err).toStrictEqual({ fail: 'fail' });
      done();
    });
  });

  it('has delete', done => {
    store.state.containers!.list = _clone(testContainersObj);
    mockAxios.delete.mockResolvedValue({
      data: { status: 'ok' },
    });
    const promise = store.dispatch('containers/delete', testContainersObj[0]);
    expect(store.state.containers!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/containers/${testContainersObj[0].entityName}/${testContainersObj[0].collectionName}/${testContainersObj[0].name}`)
      expect(store.state.containers!.status).toBe('success');
      expect(store.state.containers!.list).toHaveLength(1);
      const deleted = _find(store.state.containers!.list, c => c.id === testContainersObj[0].id);
      expect(deleted).toBeUndefined();
      done();
    });
  });
  it('has delete fail', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch(`containers/delete`, testContainersObj[0])
      .catch(err => {
        expect(store.state.containers!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  })

});