import { shallowMount, createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import Vue from 'vue';

import App from '@/App.vue';

Vue.use(Vuetify);

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(VueRouter);

describe('App.vue', () => {
  let getters;
  let store: any;
  let vuetify: any;

  beforeEach(() => {
    getters = {
      isLoggedIn: () => true,
      currentUser: () => { return { fullname: 'Test Hase' } },
      showSnackbar: () => false,
      snackbarMsg: () => '',
    }
    store = new Vuex.Store({ getters });
    vuetify = new Vuetify();
  });

  it('has title', () => {
    const wrapper = shallowMount(App, { localVue, store, vuetify });
    expect(wrapper.text()).toContain('Hinkskalle');
  });
});