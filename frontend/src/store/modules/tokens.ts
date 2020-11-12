import { Module } from 'vuex';

import { Token, plainToToken, serializeToken } from '../models';

import { map as _map, filter as _filter, concat as _concat } from 'lodash';
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
    tokensLoadingSucceeded(state: State) {
      state.status = 'success';
    },
    setList(state: State, tokens: Token[]) {
      state.tokens = tokens;
    },
    updateToken(state: State, token: Token) {
      state.tokens = _concat(_filter(state.tokens, t => t.id !== token.id), token);
    },
    removeToken(state: State, id: string) {
      state.tokens = _filter(state.tokens, t => t.id !== id);
    }
  },
  actions: {
    list: ({ commit, rootState }): Promise<Token[]> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.get(`/v1/users/${rootState.currentUser.username}/tokens`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToToken);
            commit('tokensLoadingSucceeded');
            commit('setList', list)
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('tokensLoadingFailed', err);
            reject(err);
          })
      });
    },
    update: ({ commit, rootState }, update: Token): Promise<Token> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.put(`/v1/users/${rootState.currentUser.username}/tokens/${update.id}`, serializeToken(update))
          .then((response: AxiosResponse) => {
            const updated = plainToToken(response.data.data);
            commit('tokensLoadingSucceeded');
            commit('updateToken', updated);
            resolve(updated);
          })
          .catch((err: AxiosError) => {
            commit('tokensLoadingFailed', err);
            reject(err);
          });
      });
    },
    create: ({ commit, rootState }, create: Token): Promise<Token> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.post(`/v1/users/${rootState.currentUser.username}/tokens`, serializeToken(create))
          .then((response: AxiosResponse) => {
            const created = plainToToken(response.data.data)
            commit('tokensLoadingSucceeded');
            commit('updateToken', created);
            resolve(created);
          })
          .catch((err: AxiosError) => {
            commit('tokensLoadingFailed', err);
            reject(err);
          });
      });
    },
    delete: ({ commit, rootState }, id: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.delete(`/v1/users/${rootState.currentUser.username}/tokens/${id}`)
          .then((response: AxiosResponse) => {
            commit('tokensLoadingSucceeded');
            commit('removeToken', id);
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('tokensLoadingFailed', err);
            reject(err);
          });
      });
    },
  },
};

export default tokenModule;