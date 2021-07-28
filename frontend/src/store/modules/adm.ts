import { Module } from 'vuex';

import { AxiosError, AxiosResponse } from 'axios';
import {Job, plainToJob, AdmLdapSyncResults, LdapPing, LdapStatus, plainToAdmLdapSyncResults, plainToLdapPing, plainToLdapStatus} from '../models';
import { plainToAdmExpireImagesResults, plainToAdmUpdateQuotasResults, AdmUpdateQuotasResults, AdmExpireImagesResults } from '../models';
import { values as _values, setWith as _setWith, clone as _clone } from 'lodash';

export const AdmKeys = {
  ExpireImages: "expire_images",
  CheckQuotas: "check_quotas",
  LdapSyncResults: "ldap_sync_results",
} as const;
type AdmKey = typeof AdmKeys[keyof typeof AdmKeys];

const AdmConverters = {
  [AdmKeys.ExpireImages]: plainToAdmExpireImagesResults,
  [AdmKeys.CheckQuotas]: plainToAdmUpdateQuotasResults,
  [AdmKeys.LdapSyncResults]: plainToAdmLdapSyncResults,
};

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  ldapStatus: LdapStatus | null;
  ldapPingResponse: LdapPing | null;
  slots: AdmKey[];
  admKeys: {
    [AdmKeys.ExpireImages]: AdmExpireImagesResults | null;
    [AdmKeys.CheckQuotas]: AdmUpdateQuotasResults | null;
    [AdmKeys.LdapSyncResults]: AdmLdapSyncResults | null;
  };
  activeJobs: {
    [AdmKeys.ExpireImages]: Job | null;
    [AdmKeys.CheckQuotas]: Job | null;
    [AdmKeys.LdapSyncResults]: Job | null;
  };
}

const admModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    ldapStatus: null,
    ldapPingResponse: null,
    slots: _values(AdmKeys),
    admKeys: {
      [AdmKeys.ExpireImages]: null,
      [AdmKeys.CheckQuotas]: null,
      [AdmKeys.LdapSyncResults]: null,
    },
    activeJobs: {
      [AdmKeys.ExpireImages]: null,
      [AdmKeys.CheckQuotas]: null,
      [AdmKeys.LdapSyncResults]: null,
    }
  },
  getters: {
    status: (state): string => state.status,
    slots: (state): string[] => state.slots,
    ldapStatus: (state): LdapStatus | null => state.ldapStatus,
    ldapPing: (state): LdapPing | null => state.ldapPingResponse,
    ldapSyncResults: (state): AdmLdapSyncResults | null => state.admKeys[AdmKeys.LdapSyncResults],
    ldapSyncJob: (state): Job | null => state.activeJobs[AdmKeys.LdapSyncResults],
    admKeys: (state) => state.admKeys,
    activeJobs: (state) => state.activeJobs,
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
    setLdapSyncJob(state: State, job: Job | null) {
      state.activeJobs[AdmKeys.LdapSyncResults] = job;
    },
    setAdmKey(state: State, newVal: { key: AdmKey; val: AdmLdapSyncResults & AdmUpdateQuotasResults & AdmExpireImagesResults | null }) {
      state.admKeys = _setWith(_clone(state.admKeys), newVal.key, newVal.val, _clone);
    },
    setActiveJob(state: State, newVal: { key: AdmKey; val: Job | null}) {
      state.activeJobs = _setWith(_clone(state.activeJobs), newVal.key, newVal.val, _clone);
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
    admResults: ({ commit, rootState }, key: AdmKey): Promise<AdmLdapSyncResults | AdmUpdateQuotasResults | AdmExpireImagesResults> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/adm/${key}`)
          .then((response: AxiosResponse) => {
            const result = AdmConverters[key](response.data.data.val);
            commit('succeeded');
            commit('setAdmKey', { key: key, val: result });
            resolve(result);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    ldapSyncResults: ({ dispatch }): Promise<AdmLdapSyncResults> => {
      return dispatch('admResults', AdmKeys.LdapSyncResults);
    },
    syncLdap: ({ dispatch }): Promise<Job | null> => {
      return dispatch('runTask', AdmKeys.LdapSyncResults);
    },
    runTask: ({ rootState, commit }, task: AdmKey): Promise<Job | null> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/adm/${task}/run`)
          .then((response: AxiosResponse) => {
            const jobInfo = plainToJob(response.data.data);
            commit('setActiveJob', { key: task, val: jobInfo });
            commit('succeeded');
            resolve(jobInfo);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    syncLdapStatus: ({ dispatch }): Promise<Job | null> => {
      return dispatch('taskStatus', AdmKeys.LdapSyncResults);
    },
    taskStatus: ({ state, commit, dispatch }, task: AdmKey): Promise<Job | null> => {
      return new Promise((resolve, reject) => {
        if (state.activeJobs[task] === null) {
          return resolve(null);
        }
        dispatch('jobInfo', state.activeJobs[task]?.id)
          .then(res => {
            commit('setActiveJob', { key: task, val: res });
            resolve(res);
          })
          .catch(err => {
            reject(err);
          });
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