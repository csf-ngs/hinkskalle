import { Module } from 'vuex';

import { Token, plainToToken, serializeToken, User } from '../models';

import { map as _map, filter as _filter, concat as _concat } from 'lodash';
import {AxiosError, AxiosInstance, AxiosResponse} from 'axios';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  tokens: Token[];
  user: User | null;
}

const tokenModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    tokens: [],
    user: null,
  },
  getters: {
    status: (state): string => state.status,
    tokens: (state): Token[] => state.tokens,
    user: (state, getters, rootState): User => state.user || rootState.currentUser,
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
    },
    setActiveUser(state: State, user: User | null) {
      state.user = user;
    }
  },
  actions: {
    list: ({ commit, rootState, getters }): Promise<Token[]> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.get(`/v1/users/${getters.user.username}/tokens`)
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
    update: ({ commit, rootState, getters }, update: Token): Promise<Token> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.put(`/v1/users/${getters.user.username}/tokens/${update.id}`, serializeToken(update))
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
    create: ({ commit, rootState, getters }, create: Token): Promise<Token> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.post(`/v1/users/${getters.user.username}/tokens`, serializeToken(create))
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
    delete: ({ commit, rootState, getters }, id: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        commit('tokensLoading');
        rootState.backend.delete(`/v1/users/${getters.user.username}/tokens/${id}`)
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
    requestDownload: ({ commit, rootState }, req: { id: string; type: string }): Promise<string> => {
      return new Promise((resolve, reject) => {
        (rootState.backend as AxiosInstance).post(`/v1/get-download-token`, req, { maxRedirects: 0})
          .then((response: AxiosResponse) => {
            resolve(response.data.location);
          })
          .catch((err: AxiosError) => {
            reject(err);
          });
      });
    },
  },
};

export default tokenModule;