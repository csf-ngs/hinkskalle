import Vue from 'vue';
import Vuex from 'vuex';

import axios, {AxiosInstance} from 'axios';

import { getEnv } from '@/util/env'

Vue.use(Vuex);

import { PassKey, ConfigParams, User, plainToUser, serializeUser, plainToConfigParams, plainToPassKey } from './models';
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
import passkeysModule, { State as PasskeysState } from './modules/passkeys';

interface State {
  backend: AxiosInstance;
  authToken: string;
  authStatus: '' | 'loading' | 'failed' | 'success';
  currentUser: User | null;
  config: ConfigParams | null;
  showDrawer: boolean;
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
  passkeys?: PasskeysState;
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
  config: null,
  showDrawer: true,
};

export default new Vuex.Store({
  state: state,
  getters: {
    authStatus: (state): string => state.authStatus,
    isLoggedIn: (state): boolean => state.currentUser !== null,
    currentUser: (state): User | null => state.currentUser,
    showDrawer: (state): boolean => state.showDrawer,
    config: (state): ConfigParams | null => state.config,
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
    toggleDrawer(state: State) {
      state.showDrawer = !state.showDrawer;
    },
    setConfig(state: State, config: ConfigParams) {
      state.config = config;
    },
  },
  actions: {
    getConfig: ({state, commit }) => {
      return new Promise((resolve, reject) => {
        state.backend.get('/assets/config/config.prod.json')
          .then(response => {
            commit('setConfig', plainToConfigParams(response.data.params));
            resolve(response);
          })
          .catch(err => {
            commit('setConfig', null);
            reject(err);
          });
      });
    },
    requestAuth: ({state, commit }, user: {username: string; password: string}) => {
      return new Promise((resolve, reject) => {
        commit('authRequested');
        state.backend.post('/v1/get-token', { username: user.username, password: user.password })
          .then(response => {
            const token = response.data.data.generatedToken;
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
    getAuthnCreateOptions: ({ state }) => {
      return new Promise<CredentialCreationOptions>((resolve) => {
        state.backend.get('/v1/webauthn/create-options')
          .then(response => {
            const config = response.data.data;
            config.publicKey.user.id = Uint8Array.from(atob(config.publicKey.user.id), c => c.charCodeAt(0));
            config.publicKey.excludeCredentials = config.publicKey.excludeCredentials.map((cred: any) => {
              cred.id = Uint8Array.from(atob(cred.id), c => c.charCodeAt(0));
              return cred;
            });
            config.publicKey.challenge = Uint8Array.from(atob(config.publicKey.challenge), c => c.charCodeAt(0));
            resolve(config);
        })
      });
    },
    registerCredential: ({ state }, cred) => {
      return new Promise<PassKey>((resolve, reject) => {
        state.backend.post('/v1/webauthn/register', cred)
          .then(response => {
            resolve(plainToPassKey(response.data.data));
          })
          .catch(err => {
            reject(err);
          });
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
    passkeys: passkeysModule,
  }
});
