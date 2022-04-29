import { Module } from 'vuex';

import { Group, GroupMember, plainToGroup, plainToGroupMember, serializeGroup, serializeGroupMember } from '../models';

import { AxiosError, AxiosResponse } from 'axios';

import { map as _map, find as _find, concat as _concat, filter as _filter } from 'lodash';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  list: Group[];
}

const groupsModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    list: [],
  },
  getters: {
    status: (state: State): string => state.status,
    list: (state: State): Group[] => state.list,
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
    setList(state: State, list: Group[]) {
      state.list = list;
    },
    update(state: State, group: Group) {
      state.list = _concat(_filter(state.list, e => e.id !== group.id), group);
    },
    remove(state: State, id: string) {
      state.list = _filter(state.list, e => e.id !== id);
    }
  },
  actions: {
    list: ({ commit, rootState }): Promise<Group[]> => {
      return new Promise((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/groups`)
          .then((response: AxiosResponse) => {
            const list = _map(response.data.data, plainToGroup);
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
    get: ({ commit, rootState }, groupName: string): Promise<Group> => {
      return new Promise<Group>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/groups/${groupName}`)
          .then((response: AxiosResponse) => {
            const group = plainToGroup(response.data.data);
            commit('succeeded');
            commit('update', group);
            resolve(group);
          })
          .catch((err: AxiosError) => {
            commit('failed');
            reject(err);
          });
      });
    },
    create: ({ commit, rootState }, group: Group): Promise<Group> => {
      return new Promise<Group>((resolve, reject) => {
        commit('loading');
        rootState.backend.post(`/v1/groups`, serializeGroup(group, true))
          .then((response: AxiosResponse) => {
            const created = plainToGroup(response.data.data);
            commit('succeeded');
            commit('update', created);
            resolve(created);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    update: ({ commit, rootState }, group: Group): Promise<Group> => {
      return new Promise<Group>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/groups/${group.name}`, serializeGroup(group, true))
          .then((response: AxiosResponse) => {
            const updated = plainToGroup(response.data.data);
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
    setMembers: ({ commit, rootState }, group: Group): Promise<GroupMember[]> => {
      return new Promise<GroupMember[]>((resolve, reject) => {
        commit('loading');
        rootState.backend.put(`/v1/groups/${group.name}/members`, _map(group.users, ug => serializeGroupMember(ug, true)))
          .then((response: AxiosResponse) => {
            const updated = _map(response.data.data, plainToGroupMember);
            commit('succeeded');
            group.users = updated;
            commit('update', group);
            resolve(updated);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
    delete: ({ commit, rootState }, group: Group): Promise<void> => {
      return new Promise<void>((resolve, reject) => {
        commit('loading');
        rootState.backend.delete(`/v1/groups/${group.name}`)
          .then(() => {
            commit('succeeded');
            commit('remove', group.id);
            resolve();
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          });
      });
    },
  }
}

export default groupsModule;