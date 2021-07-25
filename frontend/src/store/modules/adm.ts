import { Module } from 'vuex';

import { AxiosError, AxiosResponse } from 'axios';
import {Job, plainToJob, AdmLdapSyncResults, LdapPing, LdapStatus, plainToAdmLdapSyncResults, plainToLdapPing, plainToLdapStatus} from '../models';
import { values as _values } from 'lodash';

export const AdmKeys = {
  ExpireImages: "expire_images",
  CheckQuotas: "check_quotas",
  LdapSyncResults: "ldap_sync_results",
} as const;
type AdmKey = typeof AdmKeys[keyof typeof AdmKeys];

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  ldapStatus: LdapStatus | null;
  ldapPingResponse: LdapPing | null;
  ldapSyncResults: AdmLdapSyncResults | null;
  ldapSyncJob: Job | null;
  slots: AdmKey[];
}

const admModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    ldapStatus: null,
    ldapPingResponse: null,
    ldapSyncResults: null,
    ldapSyncJob: null,
    slots: _values(AdmKeys),
  },
  getters: {
    status: (state): string => state.status,
    slots: (state): string[] => state.slots,
    ldapStatus: (state): LdapStatus | null => state.ldapStatus,
    ldapPing: (state): LdapPing | null => state.ldapPingResponse,
    ldapSyncResults: (state): AdmLdapSyncResults | null => state.ldapSyncResults,
    ldapSyncJob: (state): Job | null => state.ldapSyncJob,
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
    },
    setLdapSyncResults(state: State, newResult: AdmLdapSyncResults | null) {
      state.ldapSyncResults = newResult;
    },
    setLdapSyncJob(state: State, job: Job | null) {
      state.ldapSyncJob = job;
    },
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
    ldapPing: ({ commit, rootState }): Promise<LdapPing> => {
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
    ldapSyncResults: ({ commit, rootState }): Promise<AdmLdapSyncResults> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/adm/${AdmKeys.LdapSyncResults}`)
          .then((response: AxiosResponse) => {
            const result = plainToAdmLdapSyncResults(response.data.data.val);
            commit('succeeded');
            commit('setLdapSyncResults', result);
            resolve(result);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    syncLdap: ({ commit, rootState }): Promise<Job | null> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/ldap/sync`)
        .then((response: AxiosResponse) => {
          const jobInfo = plainToJob(response.data.data);
          commit('setLdapSyncJob', jobInfo);
          commit('succeeded');
          resolve(jobInfo);
        })
        .catch((err: AxiosError) => {
          commit('failed', err);
          reject(err);
        });
      });
    },
    syncLdapStatus: ({ state, commit, dispatch }): Promise<Job | null> => {
      return new Promise((resolve, reject) => {
        if (state.ldapSyncJob === null) {
          return resolve(null);
        }
        dispatch('jobInfo', state.ldapSyncJob.id)
          .then(res => {
            commit('setLdapSyncJob', res);
            resolve(res);
          })
          .catch(err => {
            reject(err);
          })
      });
    },
    jobInfo: ({ commit, rootState }, jobId: string): Promise<Job> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/jobs/${jobId}`)
          .then((response: AxiosResponse) => {
            const jobInfo = plainToJob(response.data.data);
            commit('succeeded');
            resolve(jobInfo);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  },
}

export default admModule;