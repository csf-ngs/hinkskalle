import { Module } from 'vuex';

import { Entity, plainToEntity, serializeEntity } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, find as _find, concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Entity[];
}

const entitiesModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state: State): string => state.status,
    list: (state: State): Entity[] => state.list,
    getByName: (state: State) => (name: string): Entity | undefined => {
      return _find(state.list, e => e.name === name)
    },
  },
  mutations: {
    loading(state: State) {
      state.status = 'loading';
    },
    succeeded(state: State) {
      state.status = 'success';
    },
    failed(state: State) {
      state.status = 'failed';
    },
    setList(state: State, list: Entity[]) {
      state.list = list;
    },
    update(state: State, entity: Entity) {
      state.list = _concat(_filter(state.list, e => e.id !== entity.id), entity);
    },
    remove(state: State, id: string) {
      state.list = _filter(state.list, e => e.id !== id);
    }
  },
  actions: {
    list: ({ commit, rootState }): Promise<Entity[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/entities`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToEntity);
            commit('succeeded');
            commit('setList', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed');
            reject(err);
          });
      });
    },
    get: ({ commit, rootState }, entityName: string): Promise<Entity> => {
      return new Promise<Entity>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/entities/${entityName}`)
          .then((response: AxiosResponse) => {
            const entity = plainToEntity(response.data.data);
            commit('succeeded');
            commit('update', entity);
            resolve(entity);
          })
          .catch((err: AxiosError) => {
            commit('failed');
            reject(err);
          });
      });
    },
    create: ({ commit, rootState }, entity: Entity): Promise<Entity> => {
      return new Promise<Entity>((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/entities`, serializeEntity(entity))
          .then((response: AxiosResponse) => {
            const created = plainToEntity(response.data.data);
            commit('succeeded');
            commit('update', created);
            resolve(created);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    update: ({ commit, rootState }, entity: Entity): Promise<Entity> => {
      return new Promise<Entity>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/entities/${entity.name}`, serializeEntity(entity))
          .then((response: AxiosResponse) => {
            const updated = plainToEntity(response.data.data);
            commit('succeeded');
            commit('update', updated);
            resolve(updated);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    delete: ({ commit, rootState }, entity: Entity): Promise<void> => {
      return new Promise<void>((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/entities/${entity.name}`)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            commit('remove', entity.id);
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  },
};

export default entitiesModule;