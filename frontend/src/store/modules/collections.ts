import { Module } from 'vuex';

import { Collection, plainToCollection } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map } from 'lodash';

interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Collection[];
}

const collectionsModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    list: (state): Collection[] => state.list,
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
    setList(state: State, list: Collection[]) {
      state.list = list;
    }
  },
  actions: {
    list: ({ commit, rootState }, entity=null): Promise<Collection[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/collections/${entity ? entity : rootState.currentUser.username}`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToCollection);
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

export default collectionsModule;