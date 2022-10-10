import { AxiosError, AxiosResponse } from 'axios';
import { Module } from 'vuex';
import { map as _map } from 'lodash';

import { PassKey, plainToPassKey, User } from '../models';

import { concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: PassKey[];
  user: User | null;
}

const passkeyModule: Module<State, any> = {
    namespaced: true,
    state: {
        status: '',
        list: [],
        user: null,
    },
    getters: {
        status: (state): string => state.status,
        list: (state): PassKey[] => state.list,
        user: (state, getters, rootState): User => state.user || rootState.currentUser,
    },
    mutations: {
        loading(state: State) {
            state.status = 'loading';
        },
        loadingFailed(state: State) {
            state.status = 'failed';
        },
        loadingSucceeded(state: State) {
            state.status = 'success';
        },
        setList(state: State, passkeys: PassKey[]) {
            state.list = passkeys;
        },
        update(state: State, pk: PassKey) {
            state.list = _concat(_filter(state.list, p => p.id !== pk.id), pk);
        },
        remove(state: State, id: string) {
            state.list = _filter(state.list, p => p.id !== id);
        },
        setActiveUser(state: State, user: User | null) {
            state.user = user;
        }
    },
    actions: {
        list: ({ commit, rootState, getters }): Promise<PassKey[]> => {
            return new Promise((resolve, reject) => {
                commit('loading');
                rootState.backend.get(`/v1/users/${getters.user.username}/passkeys`)
                    .then((response: AxiosResponse) => {
                        const list = _map(response.data.data, plainToPassKey)
                        commit('loadingSucceeded');
                        commit('setList', list);
                        resolve(list);
                    })
                    .catch((err: AxiosError) => {
                        commit('loadingFailed');
                        reject(err);
                    });
            });
        },
        delete: ({ commit, rootState, getters }, toDelete: PassKey): Promise<void> => {
            return new Promise((resolve, reject) => {
                commit('loading');
                rootState.backend.delete(`/v1/users/${getters.user.username}/passkeys/${toDelete.id}`)
                    .then(() => {
                        commit('remove', toDelete.id);
                        commit('loadingSucceeded');
                        resolve();
                    })
                    .catch((err: AxiosError) => {
                        commit('loadingFailed');
                        reject(err);
                    });
            });
        },
    },
};

export default passkeyModule;