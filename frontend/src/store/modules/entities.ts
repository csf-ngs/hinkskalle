import { Module } from 'vuex';

import { Entity, plainToEntity } from '../models';

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
  },
};

export default entitiesModule;