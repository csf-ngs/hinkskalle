import { Module } from 'vuex';

import { Upload, plainToUpload } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map } from 'lodash';


interface State {
  status: '' | 'loading' | 'failed' | 'success';
  latest: Upload[];
}

const containersModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    latest: [],
  },
  getters: {
    status: (state): string => state.status,
    latest: (state): Upload[] => state.latest,
  },
  mutations: {
    latestLoading(state: State) {
      state.status = 'loading';
    },
    latestLoadingFailed(state: State) {
      state.status = 'failed';
    },
    latestLoadingSucceeded(state: State) {
      state.status = 'success';
    },
    setLatest(state: State, uploads: Upload[]) {
      state.latest = _map(uploads, plainToUpload);
    },
  },
  actions: {
    latest: ({ state, commit, rootState }) => {
      return new Promise((resolve, reject) => {
        commit('latestLoading'),
        rootState.backend.get('/v1/latest')
          .then((response: AxiosResponse) => {
            console.log(response.data);
            commit('latestLoadingSucceeded');
            commit('setLatest', response.data.data);
            resolve(response.data);
          })
          .catch((err: AxiosError) => {
            commit('latestLoadingFailed', err);
            reject(err);
          })
      });
    },
  },
};

export default containersModule;