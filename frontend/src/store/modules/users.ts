import { Module } from 'vuex';

import { User, plainToUser, serializeUser } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

interface State {
  status: '' | 'loading' | 'failed' | 'success';
}

const userModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
  },
  getters: {
    status: (state): string => state.status,
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
  },
  actions: {
    update: ({ commit, rootState }, update: User): Promise<User> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/users/${update.id}`, serializeUser(update))
          .then((response: AxiosResponse) => {
            const updated = plainToUser(response.data.data);
            commit('succeeded');
            resolve(updated);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  },
};

export default userModule;