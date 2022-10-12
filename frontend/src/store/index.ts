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

import { b64url_decode, b64url_encode } from '@/util/b64url';

interface State {
  backend: AxiosInstance;
  authToken: string;
  authStatus: '' | 'loading' | 'failed' | 'success';
  currentUser: User | null;
  config: ConfigParams | null;
  canWebAuthn: boolean;
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
  canWebAuthn: !!navigator.credentials && !!window.PublicKeyCredential,
};

export default new Vuex.Store({
  state: state,
  getters: {
    authStatus: (state): string => state.authStatus,
    isLoggedIn: (state): boolean => state.currentUser !== null,
    currentUser: (state): User | null => state.currentUser,
    showDrawer: (state): boolean => state.showDrawer,
    config: (state): ConfigParams | null => state.config,
    canWebAuthn: (state): boolean => state.canWebAuthn,
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
    requestSignin: ({ state }, username: string) => {
      return new Promise<{ options: PublicKeyCredentialRequestOptions, passwordDisabled: boolean}>((resolve) => {
        state.backend.post('/v1/webauthn/signin-request', { username: username })
          .then(response => {
            const opts: PublicKeyCredentialRequestOptions = response.data.data.options;
            opts.allowCredentials = opts.allowCredentials?.map((cred: any) => {
              cred.id = b64url_decode(cred.id);
              return cred;
            });
            opts.challenge = b64url_decode(opts.challenge as unknown as string);
            resolve({ options: opts, passwordDisabled: !!response.data.data.passwordDisabled });
          })
      });
    },
    doSignin: ({ state, commit }, cred) => {
      return new Promise((resolve, reject) => {
        const postData = {
          id: cred.id,
          rawId: b64url_encode(cred.rawId),
          response: {
            authenticatorData: b64url_encode(cred.response.authenticatorData),
            clientDataJSON: b64url_encode(cred.response.clientDataJSON),
            signature: b64url_encode(cred.response.signature),
            userHandle: b64url_encode(cred.response.userHandle),
          },
          type: cred.type,
          clientExtensionResults: {},
          authenticatorAttachment: cred.authenticatorAttachment, 
        };
        commit('authRequested');
        state.backend.post('/v1/webauthn/signin', postData)
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
    getAuthnCreateOptions: ({ state }) => {
      return new Promise<CredentialCreationOptions>((resolve) => {
        state.backend.get('/v1/webauthn/create-options')
          .then(response => {
            const config = response.data.data;
            config.publicKey.user.id = b64url_decode(config.publicKey.user.id);
            config.publicKey.excludeCredentials = config.publicKey.excludeCredentials.map((cred: any) => {
              cred.id = b64url_decode(cred.id); 
              return cred;
            });
            config.publicKey.challenge = b64url_decode(config.publicKey.challenge);
            resolve(config);
        })
      });
    },
    registerCredential: ({ state }, data: { name: string, cred: any }) => {
      const postData = {
        name: data.name,
        credential: {
          id: data.cred.id,
          rawId: b64url_encode(data.cred.rawId),
          response: {
            attestationObject: b64url_encode(data.cred.response.attestationObject),
            clientDataJSON: b64url_encode(data.cred.response.clientDataJSON),
          },
          type: data.cred.type,
          transports: data.cred.transports,
          clientExtensionResults: data.cred.clientExtensionResults,
        },
        public_key: b64url_encode(data.cred.response.getPublicKey()),
      };
      return new Promise<PassKey>((resolve, reject) => {
        state.backend.post('/v1/webauthn/register', postData)
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
