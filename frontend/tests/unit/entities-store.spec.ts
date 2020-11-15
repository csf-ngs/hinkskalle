import store from '@/store';

import {plainToEntity} from '@/store/models';

import axios from 'axios';

import { map as _map } from 'lodash';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

import { testUser, testUserObj } from './store.spec';

store.state.backend = mockAxios;

const testEntities = [
  {
    id: 1, name: 'esel', description: 'eyore', createdAt: new Date(),
  },
  {
    id: 2, name: 'schaf', description: 'shawn', createdAt: new Date(),
  }
];

export const testEntitiesObj = _map(testEntities, plainToEntity);

describe('entity store getters', () => {
  it('has entity status getter', () => {
    store.state.entities!.status = 'loading';
    expect(store.getters['entities/status']).toBe('loading');
  });

  it('has collection list getter', () => {
    store.state.entities!.list = testEntitiesObj;
    expect(store.getters['entities/list']).toStrictEqual(testEntitiesObj);
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
});