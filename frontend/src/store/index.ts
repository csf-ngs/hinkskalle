import Vue from 'vue'
import Vuex from 'vuex'

import axios, {AxiosInstance} from 'axios';

Vue.use(Vuex)

export interface User {
  username: string,
  email: string,
  fullname: string,
  role: "admin" | "user",
  extra_data: any,
}

export interface SnackbarState {
  show: boolean,
  msg: string | null,
}

interface State {
  backend: AxiosInstance,
  snackbar: SnackbarState,
  authToken: string,
  authStatus: string,
  currentUser: User | null,
}

const state: State = {
  backend: axios.create({ baseURL: process.env.VUE_APP_BACKEND_URL }),
  snackbar: {
    show: false,
    msg: '',
  },
  authToken: '',
  authStatus: '',
  currentUser: null,
}

export default new Vuex.Store({
  state: state,
  getters: {
    authStatus: state => state.authStatus,
    isLoggedIn: state => state.currentUser !== null,
  },
  mutations: {
    openSnackbar(state: State, msg: string) {
      state.snackbar.msg = msg;
      state.snackbar.show = true;
    },
    closeSnackbar(state: State) {
      state.snackbar.msg = '';
      state.snackbar.show = false;
    },
    authRequested(state: State) {
      state.authStatus = 'loading';
    },
    authSuccess(state: State, params: { token: string, user: User }) {
      state.authToken = params.token;
      state.currentUser = params.user;
      state.authStatus = 'success';
      state.backend.defaults.headers.common['Authorization']=`Bearer ${state.authToken}`;
    },
    authFailed(state: State, error) {
      console.log(error);
      state.authStatus = 'failed';
      state.currentUser = null;
      state.authToken = '';
      delete state.backend.defaults.headers.common['Authorization'];
    },
  },
  actions: {
    requestAuth: ({state, commit, dispatch}, user: {username: string, password: string}) => {
      return new Promise((resolve, reject) => {
        commit('authRequested');
        state.backend.post('/api/v1/get-token', { username: user.username, password: user.password })
          .then(response => {
            const token = response.data.token;
            localStorage.setItem('token', token);
            const user = response.data.user as User;
            commit('authSuccess', { token, user });
            resolve(response);
          })
          .catch(err => {
            commit('authFailed', err);
            localStorage.removeItem('token');
            reject(err);
          });
      });
    },
  },
  modules: {
  }
})
