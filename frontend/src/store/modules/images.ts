import { Module } from 'vuex';
import {AxiosError, AxiosResponse} from 'axios';
import {Image, plainToImage, InspectAttributes} from '../models';
import { map as _map } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Image[];
}

const imagesModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    list: (state): Image[] => state.list,
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
    setList(state: State, list: Image[]) {
      state.list = list;
    },
  },
  actions: {
    list: ({ commit, rootState }, container: { entityName: string; collectionName: string; containerName: string }): Promise<Image[]> => {
      return new Promise<Image[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/containers/${container.entityName}/${container.collectionName}/${container.containerName}/images`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToImage);
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
    inspect: ({ commit, rootState }, image: { fullPath: string }): Promise<InspectAttributes> => {
      return new Promise<InspectAttributes>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/images/${image.fullPath}/inspect`)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            resolve(response.data.data.attributes as InspectAttributes);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  },
};

export default imagesModule;