import { Module } from 'vuex';

import { Upload, plainToUpload, Container, plainToContainer } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map } from 'lodash';


export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  latest: Upload[];
  list: Container[];
}

const containersModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    latest: [],
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    latest: (state): Upload[] => state.latest,
    list: (state): Container[] => state.list,
  },
  mutations: {
    loading(state: State) {
      state.status = 'loading';
    },
    failed(state: State) {
      state.status = 'failed';
    },
    succeeded(state: State) {
      state.status = 'success';
    },
    setLatest(state: State, uploads: Upload[]) {
      state.latest = uploads;
    },
    setList(state: State, containers: Container[]) {
      state.list = containers;
    },
  },
  actions: {
    latest: ({ commit, rootState }) => {
      return new Promise((resolve, reject) => {
        commit('loading'),
        rootState.backend.get(`/v1/latest`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToUpload);
            commit('succeeded');
            commit('setLatest', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    list: ({ commit, rootState }, path: { entity: string; collection: string }) => {
      return new Promise((resolve, reject) => {
        commit('loading'),
        rootState.backend.get(`/v1/containers/${path.entity}/${path.collection}`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToContainer);
            commit('succeeded');
            commit('setList', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  },
};

export default containersModule;