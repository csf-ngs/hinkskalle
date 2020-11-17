import store from '@/store';

import {Entity, plainToEntity, serializeEntity} from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

const testEntities = [
  {
    id: '1', name: 'esel', description: 'eyore', createdAt: new Date(),
  },
  {
    id: '2', name: 'schaf', description: 'shawn', createdAt: new Date(),
  }
];

export const testEntitiesObj = _map(testEntities, plainToEntity);

describe('entity store getters', () => {
  it('has entity status getter', () => {
    store.state.entities!.status = 'loading';
    expect(store.getters['entities/status']).toBe('loading');
  });

  it('has entity list getter', () => {
    store.state.entities!.list = testEntitiesObj;
    expect(store.getters['entities/list']).toStrictEqual(testEntitiesObj);
  });

  it('has by name getter', () => {
    store.state.entities!.list = testEntitiesObj;
    expect(store.getters['entities/getByName']('schaf')).toStrictEqual(testEntitiesObj[1]);
  });
});

describe('entity store mutations', () => {
  it('has status mutations', () => {
    store.state.entities!.status = '';
    store.commit('entities/loading');
    expect(store.state.entities!.status).toBe('loading');
    store.commit('entities/succeeded');
    expect(store.state.entities!.status).toBe('success');
    store.commit('entities/failed');
    expect(store.state.entities!.status).toBe('failed');
  });

  it('has setList mutation', () => {
    store.state.entities!.list = [];
    store.commit('entities/setList', testEntitiesObj);
    expect(store.state.entities!.list).toStrictEqual(testEntitiesObj);
  });

  it('has update mutation', () => {
    store.state.entities!.list = _clone(testEntitiesObj);
    const update = _clone(_find(testEntitiesObj, e => e.id === '1'));
    if (!update) {
      throw 'update entity test not found';
    }
    update.description = 'Impala';
    store.commit('entities/update', update);

    const updated = _find(store.state.entities!.list, e => e.id === update.id);
    expect(updated).toStrictEqual(update);
    expect(store.state.entities!.list).toHaveLength(2);

    const create = new Entity();
    create.id="999";
    create.name="superllama";
    create.createdAt = new Date();

    store.commit('entities/update', create);
    expect(store.state.entities!.list).toHaveLength(3);
    const added = _find(store.state.entities!.list, e => e.id === create.id);
    expect(added).toStrictEqual(create);
  });

  it('has remove mutation', () => {
    store.state.entities!.list = _clone(testEntitiesObj);
    const toRemove = testEntitiesObj[0];
    store.commit('entities/remove', toRemove.id);
    expect(store.state.entities!.list).toHaveLength(1);
    const removed = _find(store.state.entities!.list, e => e.id === toRemove.id);
    expect(removed).toBeUndefined();
  })

});

describe('entity store actions', () => {
  it('has load entity list', done => {
    mockAxios.get.mockResolvedValue({
      data: { data: testEntities },
    });
    const promise = store.dispatch('entities/list');
    expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/entities`);
    expect(store.state.entities!.status).toBe('loading');
    promise.then(() => {
      expect(store.state.entities!.status).toBe('success');
      expect(store.state.entities!.list).toStrictEqual(testEntitiesObj);
      done();
    });
  });
  it('has load entity list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('entities/list').catch(err => {
      expect(err).toStrictEqual({ fail: 'fail' });
      expect(store.state.entities!.status).toBe('failed');
      done();
    });
  });

  it('has get entity by name', done => {
    const returnEntity = testEntities[0];
    returnEntity.description = 'superllama!';
    const returnEntityObj = plainToEntity(returnEntity);
    mockAxios.get.mockResolvedValue({
      data: { data: returnEntity },
    });
    const promise = store.dispatch('entities/get', returnEntity.name);
    expect(store.state.entities!.status).toBe('loading');
    promise.then(entity => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/entities/${returnEntity.name}`);
      expect(store.state.entities!.status).toBe('success');
      expect(entity).toStrictEqual(returnEntityObj);
      const updated = _find(store.state.entities!.list, e => e.id === returnEntityObj.id);
      expect(updated).toStrictEqual(returnEntityObj);
      done();
    });
  });

  it('has create entity', done => {
    const entity = {
      name: 'testilein',
    };
    const createEntityObj = plainToEntity(entity);

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', name: entity.name }}
    });
    
    const promise = store.dispatch('entities/create', createEntityObj);
    expect(store.state.entities!.status).toBe('loading');
    promise.then(entity => {
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/entities`, serializeEntity(createEntityObj));
      expect(store.state.entities!.status).toBe('success');
      const created = _find(store.state.entities!.list, e => e.id === '666');
      if (!created) {
        throw Error('created id 666 not found in test entity store');
      }
      createEntityObj.id = created.id;
      expect(created).toStrictEqual(createEntityObj);
      expect(entity).toStrictEqual(createEntityObj);
      done();
    });
  });

  it('has create entity fail handling', done => {
    const entity = {
      name: "testilein",
    };
    const createEntityObj = plainToEntity(entity);
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('entities/create', createEntityObj)
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.entities!.status).toBe('failed');
        done();
      });
  });

  it('has update', done => {
    const update = _clone(_find(testEntitiesObj, e => e.id==="1"));
    if (!update) {
      throw 'test entity not found';
    }
    update.description = 'tohuwabohu';
    const updateObj = plainToEntity(update);

    mockAxios.put.mockResolvedValue({
      data: { data: update } 
    });

    store.state.entities!.list = _clone(testEntitiesObj);

    const promise = store.dispatch('entities/update', updateObj);
    expect(store.state.entities!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/entities/${updateObj.name}`, serializeEntity(updateObj));
      expect(store.state.entities!.status).toBe('success');
      expect(store.state.entities!.list).toHaveLength(2);
      const updated = _find(store.state.entities!.list, e => e.id===update.id);
      expect(updated).toStrictEqual(updateObj);
      done();
    });
  });
  it('has update fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('entities/update', testEntitiesObj[0]).catch(err => {
      expect(store.state.entities!.status).toBe('failed');
      expect(err).toStrictEqual({ fail: 'fail' });
      done();
    });
  });

  it('has delete', done => {
    store.state.entities!.list = _clone(testEntitiesObj);
    mockAxios.delete.mockResolvedValue({
      data: { status: 'ok' },
    });
    const promise = store.dispatch('entities/delete', testEntitiesObj[0]);
    expect(store.state.entities!.status).toBe('loading');
    promise.then(() => {
      expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/entities/${testEntitiesObj[0].name}`)
      expect(store.state.entities!.status).toBe('success');
      expect(store.state.entities!.list).toHaveLength(1);
      const deleted = _find(store.state.entities!.list, e => e.id === testEntitiesObj[0].id);
      expect(deleted).toBeUndefined();
      done();
    });
  });
  it('has delete fail', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch(`entities/delete`, testEntitiesObj[0])
      .catch(err => {
        expect(store.state.entities!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  })



});