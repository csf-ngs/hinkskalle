import { Module } from 'vuex';

import { Upload, plainToUpload, Container, plainToContainer, Collection, serializeContainer } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, isNil as _isNil, concat as _concat, filter as _filter } from 'lodash';


export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  latest: Upload[];
  list: Container[];
}

const containersModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    latest: [],
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    latest: (state): Upload[] => state.latest,
    list: (state): Container[] => state.list,
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
    setLatest(state: State, uploads: Upload[]) {
      state.latest = uploads;
    },
    setList(state: State, containers: Container[]) {
      state.list = containers;
    },
    update(state: State, container: Container) {
      state.list = _concat(_filter(state.list, c => c.id !== container.id), container);
    },
    remove(state: State, id: string) {
      state.list = _filter(state.list, c => c.id !== id);
    },
  },
  actions: {
    latest: ({ commit, rootState }): Promise<Upload[]> => {
      return new Promise<Upload[]>((resolve, reject) => {
        commit('loading'),
        rootState.backend.get(`/v1/latest`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToUpload);
            commit('succeeded');
            commit('setLatest', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    list: ({ commit, rootState }, path: { entityName: string; collectionName: string }): Promise<Container[]> => {
      return new Promise<Container[]>((resolve, reject) => {
        commit('loading'),
        rootState.backend.get(`/v1/containers/${path.entityName}/${path.collectionName}`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToContainer);
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
    get: ({ commit, rootState }, path: { entityName: string; collectionName: string; containerName: string }): Promise<Container> => {
      return new Promise<Container>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/containers/${path.entityName}/${path.collectionName}/${path.containerName}`)
          .then((response: AxiosResponse) => {
            const container = plainToContainer(response.data.data);
            commit('succeeded');
            resolve(container);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    create: ({ commit, rootState, dispatch }, container: Container): Promise<Container> => {
      return new Promise<Container>((resolve, reject) => {
        let getCollection: Promise<Collection>;
        if (!_isNil(container.collection)) {
          const fakeCollection = new Collection();
          fakeCollection.id=container.collection;
          getCollection = Promise.resolve(fakeCollection);
        }
        else {
          getCollection = dispatch('collections/get', container, { root: true });
        }
        commit('loading');
        getCollection
          .then(collection => {
            container.collection = collection.id;
            rootState.backend.post(`/v1/containers`, serializeContainer(container))
              .then((response: AxiosResponse) => {
                const created = plainToContainer(response.data.data);
                commit('succeeded');
                commit('update', created);
                resolve(created);
              })
              .catch((err: AxiosError) => {
                commit('failed', err);
                reject(err);
              });
          })
          .catch(err => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    update: ({ commit, rootState }, container: Container): Promise<Container> => {
      return new Promise<Container>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/containers/${container.entityName}/${container.collectionName}/${container.name}`, serializeContainer(container))
          .then((response: AxiosResponse) => {
            const updated = plainToContainer(response.data.data);
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
    delete: ({ commit, rootState }, container: Container): Promise<void> => {
      return new Promise<void>((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/containers/${container.entityName}/${container.collectionName}/${container.name}`)
          .then((response: AxiosResponse) => {
            commit('succeeded');
            commit('remove', container.id);
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });

      })

    }

  },
};

export default containersModule;