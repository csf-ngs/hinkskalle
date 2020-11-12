import Vue from 'vue';
import Vuex from 'vuex';

import axios, {AxiosInstance} from 'axios';

Vue.use(Vuex);

import { User, plainToUser } from './models';
import snackbarModule from './modules/snackbar';
import containersModule from './modules/containers';
import tokensModule from './modules/tokens';
import usersModule from './modules/users';

interface State {
  backend: AxiosInstance;
  authToken: string;
  authStatus: '' | 'loading' | 'failed' | 'success';
  currentUser: User | null;
  snackbar?: any;
  containers?: any;
  tokens?: any;
  users?: any;
}

const token = localStorage.getItem('token') || '';
if (token !== '') {
  axios.defaults.headers.common['Authorization']=`Bearer ${token}`;
}
const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
const currentUserObj: User | null = currentUser ? plainToUser(currentUser) : null;

const state: State = {
  backend: axios.create({ baseURL: process.env.VUE_APP_BACKEND_URL }),
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
    authFailed(state: State, error) {
      state.authStatus = 'failed';
      state.currentUser = null;
      state.authToken = '';
      delete state.backend.defaults.headers.common['Authorization'];
    },
    setUser(state: State, user: User) {
      state.currentUser = user;
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
      return new Promise((resolve) => {
        commit('logout');
        resolve();
      });
    },
  },
  modules: {
    snackbar: snackbarModule,
    containers: containersModule,
    tokens: tokensModule,
    users: usersModule,
  }
});
