import { AxiosError, AxiosResponse } from 'axios';
import { Module } from 'vuex';
import { map as _map } from 'lodash';

import { PassKey, plainToPassKey, serializePassKey, User } from '../models';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  passkeys: PassKey[];
  user: User | null;
}

const passkeyModule: Module<State, any> = {
    namespaced: true,
    state: {
        status: '',
        passkeys: [],
        user: null,
    },
    getters: {
        status: (state): string => state.status,
        list: (state): PassKey[] => state.passkeys,
        user: (state, getters, rootState): User => state.user || rootState.currentUser,
    },
    mutations: {
        passkeysLoading(state: State) {
        state.status = 'loading';
        },
        passkeysLoadingFailed(state: State) {
        state.status = 'failed';
        },
        passkeysLoadingSucceeded(state: State) {
        state.status = 'success';
        },
        setList(state: State, passkeys: PassKey[]) {
        state.passkeys = passkeys;
        },
        setActiveUser(state: State, user: User | null) {
            state.user = user;
        }
    },
    actions: {
        list: ({ commit, rootState, getters }): Promise<PassKey[]> => {
            return new Promise((resolve, reject) => {
                commit('passkeysLoading');
                rootState.backend.get(`/v1/users/${getters.user.username}/passkeys`)
                    .then((response: AxiosResponse) => {
                        const list = _map(response.data.data, plainToPassKey)
                        commit('passkeysLoadingSucceeded');
                        commit('setList', list);
                        resolve(list);
                    })
                    .catch((err: AxiosError) => {
                        commit('passkeysLoadingFailed');
                        reject(err);
                    });
            });
        },
    },
};

export default passkeyModule;