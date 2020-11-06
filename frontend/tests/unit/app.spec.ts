import { shallowMount, mount } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';

import App from '@/App.vue';

import { localVue } from '../setup';

describe('App.vue', () => {
  let getters: any;
  let mutations: any;
  let store: any;
  let vuetify: any;
  let router: any;

  let isLoggedIn = true;
  let showSnackbar = false;

  beforeEach(() => {
    mutations = {
      closeSnackbar: jest.fn()
    };
    getters = {
      isLoggedIn: () => isLoggedIn,
      currentUser: () => { return { fullname: 'Test Hase' } },
      showSnackbar: () => showSnackbar,
      snackbarMsg: () => '',
    };
    store = new Vuex.Store({ getters, mutations });
    vuetify = new Vuetify();
    router = new VueRouter();
  });

  it('has title', () => {
    const wrapper = shallowMount(App, { localVue, store, vuetify });
    expect(wrapper.text()).toContain('Hinkskalle');
  });

  it('shows user info', () => {
    const wrapper = shallowMount(App, { localVue, store, vuetify });
    expect(wrapper.text()).toContain('Test Hase');
  });

  it('shows not logged in', () => {
    isLoggedIn = false;
    const wrapper = shallowMount(App, { localVue, store, vuetify });
    expect(wrapper.text()).toContain('Not Logged In');
  });

  it('can hide the snackbar', () => {
    showSnackbar = true;
    const wrapper = mount(App, { localVue, store, vuetify, router });
    wrapper.find('#close-snackbar').trigger('click');
    expect(mutations.closeSnackbar).toHaveBeenCalled();
  });
});