import { Module } from 'vuex';

import { has as _has } from 'lodash';
import { AxiosError } from 'axios';

export type SnackbarType = '' | 'info' | 'success' | 'error';

interface State {
  show: boolean;
  type: SnackbarType;
  msg: string;
}

const snackbarModule: Module<State, any> = {
  namespaced: true,
  state: {
    show: false,
    type: '',
    msg: '',
  },
  getters: {
    show: (state): boolean => state.show,
    msg: (state): string => state.msg,
    type: (state): string => state.type,
  },
  mutations: {
    open(state: State, msg: string) {
      state.msg = msg;
      state.show = true;
      state.type = 'info';
    },
    close(state: State) {
      state.msg = '';
      state.show = false;
      state.type = '';
    },
    showSuccess(state: State, msg: string) {
      state.msg = msg;
      state.show = true;
      state.type = 'success';
    },
    showError(state: State, error: AxiosError | string) {
      state.type='error';
      state.show=true;

      if (typeof error === 'string') {
        state.msg = error; 
        return;
      }

      if (error.response) {
        let msg = `Code ${error.response.status}: `
        const data = error.response.data;
        if (_has(data, 'errors')) {
          msg += data.errors[0].message;
        }
        else if (_has(data, 'message')) {
          msg += data.message;
        }
        else {
          if (error.response.status === 401) {
            msg += "Unauthorized! ";
          }
          msg += error.response.statusText;
        }
        state.msg=msg;
      }
      else if (error.request) {
        state.msg="Upstream may have died, or your network sucks.";
      }
      else {
        state.msg=error.message;
      }
    },
  },
};

export default snackbarModule;