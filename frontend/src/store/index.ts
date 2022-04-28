import Vue from 'vue';
import Vuex from 'vuex';

import axios, {AxiosInstance} from 'axios';

import { getEnv } from '@/util/env'

Vue.use(Vuex);

import { User, plainToUser, serializeUser, } from './models';
import snackbarModule, { State as SnackbarState } from './modules/snackbar';
import entitiesModule, { State as EntitiesState } from './modules/entities';
import groupsModule, { State as GroupsState } from './modules/groups';
import containersModule, { State as ContainersState } from './modules/containers';
import collectionsModule, { State as CollectionsState }  from './modules/collections';
import imagesModule, { State as ImagesState } from './modules/images';
import tokensModule, { State as TokensState } from './modules/tokens';
import usersModule, { State as UsersState } from './modules/users';
import searchModule, { State as SearchState } from './modules/search';
import admModule, { State as AdmState } from './modules/adm';
import manifestsModule, { State as ManifestsState } from './modules/manifests';

interface State {
  backend: AxiosInstance;
  authToken: string;
  authStatus: '' | 'loading' | 'failed' | 'success';
  currentUser: User | null;
  snackbar?: SnackbarState;
  tokens?: TokensState;
  users?: UsersState;
  images?: ImagesState;
  containers?: ContainersState;
  collections?: CollectionsState;
  entities?: EntitiesState;
  groups?: GroupsState;
  search?: SearchState;
  adm?: AdmState;
  manifests?: ManifestsState;
}

const token = localStorage.getItem('token') || '';
if (token !== '') {
  axios.defaults.headers.common['Authorization']=`Bearer ${token}`;
}
const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
const currentUserObj: User | null = currentUser ? plainToUser(currentUser) : null;

const state: State = {
  backend: axios.create({ baseURL: getEnv('VUE_APP_BACKEND_URL') as string }),
  authToken: token,
  authStatus: '',
  currentUser: currentUserObj,
};

export default new Vuex.Store({
  state: state,
  getters: {
    authStatus: (state): string => state.authStatus,
    isLoggedIn: (state): boolean => state.currentUser !== null,
    currentUser: (state): User | null => state.currentUser,
  },
  mutations: {
    registerInterceptor(state: State, func: (err: any) => Promise<void>) {
      state.backend.interceptors.response.use(undefined, func);  
    },
    authRequested(state: State) {
      state.authStatus = 'loading';
    },
    authSuccess(state: State, params: { token: string; user: User }) {
      state.authToken = params.token;
      state.currentUser = params.user;
      state.authStatus = 'success';
      state.backend.defaults.headers.common['Authorization']=`Bearer ${state.authToken}`;
    },
    authFailed(state: State) {
      state.authStatus = 'failed';
      state.currentUser = null;
      state.authToken = '';
      delete state.backend.defaults.headers.common['Authorization'];
    },
    setUser(state: State, user: User) {
      state.currentUser = user;
      localStorage.setItem('user', JSON.stringify(serializeUser(user)));
    },
    logout(state: State) {
      state.authToken = '';
      state.currentUser = null;
      state.authStatus = '';
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete(state.backend.defaults.headers.common['Authorization']);
    },
  },
  actions: {
    requestAuth: ({state, commit }, user: {username: string; password: string}) => {
      return new Promise((resolve, reject) => {
        commit('authRequested');
        state.backend.post('/v1/get-token', { username: user.username, password: user.password })
          .then(response => {
            const token = response.data.data.token;
            localStorage.setItem('token', token);
            const user = plainToUser(response.data.data.user);
            localStorage.setItem('user', JSON.stringify(response.data.data.user));
            commit('authSuccess', { token, user });
            commit('users/reset');
            resolve(response);
          })
          .catch(err => {
            commit('authFailed', err);
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            reject(err);
          });
      });
    },
    logout: ({ commit }) => {
      return new Promise<void>((resolve) => {
        commit('logout');
        commit('users/reset');
        resolve();
      });
    },
  },
  modules: {
    snackbar: snackbarModule,
    tokens: tokensModule,
    users: usersModule,
    images: imagesModule,
    containers: containersModule,
    collections: collectionsModule,
    entities: entitiesModule,
    groups: groupsModule,
    search: searchModule,
    adm: admModule,
    manifests: manifestsModule,
  }
});
