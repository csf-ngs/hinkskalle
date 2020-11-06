import Vue from 'vue';
import Vuex from 'vuex';

import axios, {AxiosInstance} from 'axios';

Vue.use(Vuex);

export interface User {
  username: string;
  email: string;
  firstname: string;
  lastname: string;
  fullname?: string;
  is_admin: boolean;
  role?: "admin" | "user";
  // eslint-disable-next-line
  extra_data?: any;
}

function prepareUser(user: User): User {
  user.fullname = `${user.firstname} ${user.lastname}`;
  user.role = user.is_admin ? 'admin' : 'user';
  return user;
}

export interface SnackbarState {
  show: boolean;
  msg: string | null;
}

interface State {
  backend: AxiosInstance;
  snackbar: SnackbarState;
  authToken: string;
  authStatus: string;
  currentUser: User | null;
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
};

export default new Vuex.Store({
  state: state,
  getters: {
    authStatus: (state): string => state.authStatus,
    isLoggedIn: (state): boolean => state.currentUser !== null,
    currentUser: (state): User | null => state.currentUser,
    showSnackbar: (state): boolean => state.snackbar.show,
    snackbarMsg: (state): string | null => state.snackbar.msg,
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
    authSuccess(state: State, params: { token: string; user: User }) {
      state.authToken = params.token;
      state.currentUser = prepareUser(params.user);
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
    setUser(state: State, user: User) {
      state.currentUser = prepareUser(user);
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
            const user = response.data.data.user as User;
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
});
