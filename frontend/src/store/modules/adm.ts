import { Module } from 'vuex';

import { AxiosError, AxiosResponse } from 'axios';
import {LdapStatus, plainToLdapStatus} from '../models';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  ldapStatus: LdapStatus | null;
}

const admModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    ldapStatus: null,
  },
  getters: {
    status: (state): string => state.status,
    ldapStatus: (state): LdapStatus | null => state.ldapStatus,
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
    setLdapStatus(state: State, newStatus: LdapStatus) {
      state.ldapStatus = newStatus;
    }
  },
  actions: {
    ldapStatus: ({ state, commit, rootState }, param: { reload?: boolean } = {}): Promise<LdapStatus> => {
      return new Promise((resolve, reject) => {
        if (state.ldapStatus !== null && !param.reload) {
          return resolve(state.ldapStatus);
        }
        commit('loading');
        rootState.backend.get(`/v1/ldap/status`)
          .then((response: AxiosResponse) => {
            const newStatus = plainToLdapStatus(response.data.data);
            commit('succeeded');
            commit('setLdapStatus', newStatus);
            resolve(newStatus);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            commit('setLdapStatus', null);
            reject(err);
          });
      });
    },
  },
}

export default admModule;