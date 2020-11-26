import { Module } from 'vuex';

import { User, plainToUser, serializeUser, Container, plainToContainer } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  starred: Container[];
}

const userModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    starred: [],
  },
  getters: {
    status: (state): string => state.status,
    starred: (state): Container[] => state.starred,
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
    setStarred(state: State, containers: Container[]) {
      state.starred = containers;
    }
  },
  actions: {
    update: ({ commit, rootState }, update: User): Promise<User> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/users/${update.username}`, serializeUser(update))
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
    delete: ({ commit, rootState }, toDelete: User): Promise<void> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/users/${toDelete.username}`)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    getStarred: ({ commit, rootState }, user: User): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/users/${user.username}/stars`)
          .then((response: AxiosResponse) => {
            const containers = _map(response.data.data, plainToContainer);
            commit('succeeded');
            commit('setStarred', containers);
            resolve(containers);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    addStar: ({ commit, rootState }, payload: { user: User; container: Container }): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/users/${payload.user.username}/stars/${payload.container.id}`)
          .then((response: AxiosResponse) => {
            const containers = _map(response.data.data, plainToContainer);
            commit('succeeded');
            commit('setStarred', containers);
            resolve(containers);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    removeStar: ({ commit, rootState }, payload: { user: User; container: Container }): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/users/${payload.user.username}/stars/${payload.container.id}`)
          .then((response: AxiosResponse) => {
            const containers = _map(response.data.data, plainToContainer);
            commit('succeeded');
            commit('setStarred', containers);
            resolve(containers);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    }
  },
};

export default userModule;