import { Module } from 'vuex';

import { Entity, plainToEntity } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map } from 'lodash';

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
    status: (state): string => state.status,
    list: (state): Entity[] => state.list,
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
  },
};

export default entitiesModule;