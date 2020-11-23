import { Module } from 'vuex';
import {AxiosError, AxiosResponse} from 'axios';
import {Image, plainToImage, InspectAttributes} from '../models';
import { map as _map, concat as _concat, filter as _filter } from 'lodash';

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
    update(state: State, upd: Image) {
      state.list = _concat(_filter(state.list, i => i.id !== upd.id ), upd);
    },
    remove(state: State, toRemove: { id: string }) {
      state.list = _filter(state.list, i => i.id !== toRemove.id);
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
    update: ({ commit, rootState }, image: Image): Promise<Image> => {
      return new Promise<Image>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/images/${image.fullPath}`, image)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            const upd = plainToImage(response.data.data);
            commit('update', upd);
            resolve(upd);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    updateTags: ({ commit, rootState }, image: { fullPath: string; tags: string[] }): Promise<string[]> => {
      return new Promise<string[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/images/${image.fullPath}/tags`, { tags: image.tags })
          .then((response: AxiosResponse) => {
            commit('succeeded');
            image.tags = response.data.data.tags;
            commit('update', image);
            resolve(image.tags);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    delete: ({ commit, rootState }, image: { id: string; fullPath: string }): Promise<void> => {
      return new Promise<void>((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/images/${image.fullPath}`)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            commit('remove', { id: image.id });
            resolve();
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