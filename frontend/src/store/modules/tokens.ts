import { Module } from 'vuex';

import { Token, plainToToken } from '../models';

import { map as _map } from 'lodash';
import {AxiosError, AxiosResponse} from 'axios';

interface State {
  status: '' | 'loading' | 'failed' | 'success';
  tokens: Token[];
}

const tokenModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    tokens: [],
  },
  getters: {
    status: (state): string => state.status,
    tokens: (state): Token[] => state.tokens,
  },
  mutations: {
    tokensLoading(state: State) {
      state.status = 'loading';
    },
    tokensLoadingFailed(state: State) {
      state.status = 'failed';
    },
    tokensLoadingSucceeded(state: State, tokens: any[]) {
      state.status = 'success';
      state.tokens = _map(tokens, plainToToken);
    },
  },
  actions: {
    list: ({ state, commit, rootState }) => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.get(`/v1/users/${rootState.currentUser.username}/tokens`)
          .then((response: AxiosResponse) => {
            commit('tokensLoadingSucceeded', response.data.data);
            resolve(response.data);
          })
          .catch((err: AxiosError) => {
            commit('tokensLoadingFailed', err);
            reject(err);
          })
      });
    },
  },
};

export default tokenModule;