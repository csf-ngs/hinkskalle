import { Module } from 'vuex';

import { Collection, Entity, plainToCollection, serializeCollection } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, isNil as _isNil, concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Collection[];
}

const collectionsModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state): string => state.status,
    list: (state): Collection[] => state.list,
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
    setList(state: State, list: Collection[]) {
      state.list = list;
    },
    update(state: State, collection: Collection) {
      state.list = _concat(_filter(state.list, t => t.id !== collection.id), collection);
    }
  },
  actions: {
    list: ({ commit, rootState }, entity=null): Promise<Collection[]> => {
      return new Promise<Collection[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/collections/${entity ? entity : rootState.currentUser.username}`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToCollection);
            commit('succeeded');
            commit('setList', list);
            resolve(list);
          })
          .catch((err: AxiosError) => {
            commit('failed');
            reject(err);
          });
      });
    },
    create: ({ commit, rootState, dispatch }, collection: Collection): Promise<Collection> => {
      return new Promise<Collection>((resolve, reject) => {
        let getEntity: Promise<Entity>;
        if (!_isNil(collection.entity)) {
          const fakeEntity = new Entity();
          fakeEntity.id=collection.entity;
          getEntity = Promise.resolve(fakeEntity);
        }
        else {
          if (_isNil(collection.entityName)) {
            collection.entityName = rootState.currentUser.username;
          }
          getEntity = dispatch('entities/get', collection.entityName, { root: true });
        }
        commit('loading');
        getEntity.then(entity => {
          collection.entity = entity.id;
          rootState.backend.post(`/v1/collections`, serializeCollection(collection))
            .then((response: AxiosResponse) => {
              const created = plainToCollection(response.data.data);
              commit('succeeded');
              commit('update', created);
              resolve(created);
            })
            .catch((err: AxiosError) => {
              commit('failed', err);
              reject(err);
            });
        });
      });
    },
  },
};

export default collectionsModule;