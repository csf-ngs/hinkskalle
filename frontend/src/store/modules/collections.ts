import { Module } from 'vuex';

import { Collection, Entity, plainToCollection, serializeCollection } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, isNil as _isNil, concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Collection[];
  currentEntity: Entity | null;
}

const collectionsModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
    currentEntity: null,
  },
  getters: {
    status: (state): string => state.status,
    list: (state): Collection[] => state.list,
    currentEntity: (state): Entity | null => state.currentEntity,
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
      state.list = _concat(_filter(state.list, c => c.id !== collection.id), collection);
    },
    remove(state: State, id: string) {
      state.list = _filter(state.list, c => c.id !== id);
    },
    setEntity(state: State, entity: Entity) {
      state.currentEntity = entity;
    },
  },
  actions: {
    list: ({ commit, rootState, dispatch }, entity=null): Promise<Collection[]> => {
      return new Promise<Collection[]>((resolve, reject) => {
        commit('loading');
        dispatch('entities/get', entity ? entity : rootState.currentUser.username, { root: true })
          .then(entity => {
            commit('setEntity', entity);
            return rootState.backend.get(`/v1/collections/${entity.name}`);
          })
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
    get: ({ commit, rootState }, path: { entityName: string; collectionName: string }): Promise<Collection> => {
      return new Promise<Collection>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/collections/${path.entityName}/${path.collectionName}`)
          .then((response: AxiosResponse) => {
            const collection = plainToCollection(response.data.data);
            commit('succeeded');
            resolve(collection);
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
        getEntity
          .then(entity => {
            collection.entity = entity.id;
            return rootState.backend.post(`/v1/collections`, serializeCollection(collection));
          })
          .then((response: AxiosResponse) => {
                const created = plainToCollection(response.data.data);
                commit('succeeded');
                commit('update', created);
                resolve(created);
          })
          .catch(err => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    update: ({ commit, rootState }, collection: Collection): Promise<Collection> => {
      return new Promise<Collection>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/collections/${collection.entityName}/${collection.name}`, serializeCollection(collection))
          .then((response: AxiosResponse) => {
            const updated = plainToCollection(response.data.data);
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
    delete: ({ commit, rootState }, collection: Collection): Promise<void> => {
      return new Promise<void>((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/collections/${collection.entityName}/${collection.name}`)
          .then(() => {
            commit('succeeded');
            commit('remove', collection.id);
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

export default collectionsModule;