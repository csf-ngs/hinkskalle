import { Module } from 'vuex';

interface State {
  show: boolean;
  msg: string;
};

const snackbarModule: Module<State, any> = {
  namespaced: true,
  state: {
    show: false,
    msg: '',
  },
  getters: {
    show: (state): boolean => state.show,
    msg: (state): string => state.msg,
  },
  mutations: {
    open(state: State, msg: string) {
      state.msg = msg;
      state.show = true;
    },
    close(state: State) {
      state.msg = '';
      state.show = false;
    },
  },
};

export default snackbarModule;