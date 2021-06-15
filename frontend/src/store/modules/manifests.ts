import { Module } from 'vuex';

import {AxiosError, AxiosResponse} from 'axios';
import { Manifest, plainToManifest } from '../models';

import { map as _map } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Manifest[];
}

const manifestsModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    list: (state): Manifest[] => state.list,
  },
  mutations: {
    loading(state: State) {
      state.status = 'loading';
    },
    succeeded(state: State) {
      state.status = 'success';
    },
    failed(state: State) {
      state.status = 'failed';
    },
    setList(state: State, list: Manifest[]) {
      state.list = list;
    },
  },
  actions: {
    list: ({ commit, rootState }, container: { entityName: string; collectionName: string; containerName: string }): Promise<Manifest[]> => {
      return new Promise<Manifest[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/containers/${container.entityName}/${container.collectionName}/${container.containerName}/manifests`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToManifest);
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
    getConfig: ({ commit, rootState }, manifest: Manifest): Promise<any> => {
      return new Promise<any>((resolve, reject) => {
        if (!manifest.content.config || !manifest.content.config.digest) {
          reject("Invalid manifest config");
        }
        commit('loading');
        rootState.backend.get(`/v2/${manifest.path}/blobs/${manifest.content.config.digest}`)
          .then((response: AxiosResponse) => {
            commit(`succeeded`);
            resolve(response.data)
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  }
}

export default manifestsModule;