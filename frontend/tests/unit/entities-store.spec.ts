import store from '@/store';

import {Entity, plainToEntity} from '@/store/models';

import axios from 'axios';

import { map as _map, clone as _clone, find as _find } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import { testUser, testUserObj } from './store.spec';

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
});