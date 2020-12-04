import { Module } from 'vuex';

import { User, plainToUser, serializeUser, Container, plainToContainer, UserQuery } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  starred: Container[];
  starsLoaded: boolean;
  list: User[];
  searchResult: User[];
}

const userModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    starred: [],
    starsLoaded: false,
    list: [],
    searchResult: [],
  },
  getters: {
    status: (state): string => state.status,
    starred: (state): Container[] => state.starred,
    list: (state): User[] => state.list,
    searchResult: (state): User[] => state.searchResult,
  },
  mutations: {
    reset(state: State) {
      state.starred = [];
      state.starsLoaded = false;
      state.searchResult = [];
    },
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
    },
    setList(state: State, users: User[]) {
      state.list = users;
    },
    update(state: State, user: User) {
      state.list = _concat(_filter(state.list, u=> u.id !== user.id), user);
    },
    remove(state: State, id: string) {
      state.list = _filter(state.list, u => u.id !== id);
    },
    setSearchResult(state: State, users: User[]) {
      state.searchResult = users;
    },
  },
  actions: {
    list: ({ commit, rootState }): Promise<User[]> => {
      return new Promise<User[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.get('/v1/users')
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToUser);
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
    search: ({ commit, rootState}, search: UserQuery): Promise<User[]> => {
      return new Promise<User[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.get('/v1/users', { params: search })
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToUser);
            commit('succeeded');
            commit('setSearchResult', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });

      });
    },
    create: ({ commit, rootState }, create: User): Promise<User> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/users`, serializeUser(create))
          .then((response: AxiosResponse) => {
            const created = plainToUser(response.data.data);
            commit('succeeded');
            commit('update', created);
            resolve(created);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    update: ({ commit, rootState }, update: User): Promise<User> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/users/${update.username}`, serializeUser(update))
          .then((response: AxiosResponse) => {
            const updated = plainToUser(response.data.data);
            commit('succeeded');
            commit('update', updated);
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
            commit('remove', toDelete.id);
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    getStarred: ({ state, commit, rootState }): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        if (state.starsLoaded) {
          return resolve(state.starred);
        }
        commit('loading');
        rootState.backend.get(`/v1/users/${rootState.currentUser.username}/stars`)
          .then((response: AxiosResponse) => {
            state.starsLoaded=true;
            const containers = _map(response.data.data, plainToContainer);
            commit('succeeded');
            commit('setStarred', containers);
            resolve(containers);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            state.starsLoaded=false;
            reject(err);
          });
      });
    },
    addStar: ({ commit, rootState }, container: Container): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/users/${rootState.currentUser.username}/stars/${container.id}`)
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
    removeStar: ({ commit, rootState }, container: Container): Promise<Container[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/users/${rootState.currentUser.username}/stars/${container.id}`)
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