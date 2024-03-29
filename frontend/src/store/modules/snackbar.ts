import { Module } from 'vuex';

import { has as _has, each as _each, isString as _isString } from 'lodash';
import { AxiosError } from 'axios';

export function generateMsg(error: AxiosError): string {
  let msg = 'unknown';
  if (error.response) {
    msg = `Code ${error.response.status}: `
    const data = error.response.data as any;
    console.log(data);
    if (_has(data, 'errors')) {
      _each(data.errors, (v,k) => {
        if (_isString(v)) {
          msg += `${k}: ${v}; `;
        }
        else if (_has(v, 'detail')) {
          msg += v.detail;
        }
        else if (_has(v, 'message')) {
          msg += v.message;
        }
        else {
          msg += v.code;
        }
      });
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
  }
  else if (error.request) {
    msg="Upstream may have died, or your network sucks.";
  }
  else {
    msg=error.message;
  }
  return msg;
}


export type SnackbarType = '' | 'info' | 'success' | 'error';

export interface State {
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
      state.msg = generateMsg(error);
    },
  },
};

export default snackbarModule;