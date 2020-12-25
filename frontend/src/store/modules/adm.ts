import { Module } from 'vuex';

import { AxiosError, AxiosResponse } from 'axios';
import {LdapPing, LdapStatus, plainToLdapPing, plainToLdapStatus} from '../models';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  ldapStatus: LdapStatus | null;
  ldapPingResponse: LdapPing | null;
}

const admModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    ldapStatus: null,
    ldapPingResponse: null,
  },
  getters: {
    status: (state): string => state.status,
    ldapStatus: (state): LdapStatus | null => state.ldapStatus,
    ldapPing: (state): LdapPing | null => state.ldapPingResponse,
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
    setLdapStatus(state: State, newStatus: LdapStatus | null) {
      state.ldapStatus = newStatus;
    },
    setLdapPing(state: State, newResult: LdapPing | null) {
      state.ldapPingResponse = newResult;
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
    ldapPing: ({ state, commit, rootState }): Promise<LdapPing> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/ldap/ping`)
          .then((response: AxiosResponse) => {
            const newResult = plainToLdapPing(response.data.data);
            commit('succeeded');
            commit('setLdapPing', newResult);
            resolve(newResult);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            commit('setLdapPing', null);
            reject(err);
          });
      });
    },
  },
}

export default admModule;