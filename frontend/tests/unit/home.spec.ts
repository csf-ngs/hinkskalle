import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import Home from '@/views/Home.vue';

import { localVue } from '../setup';

describe('Home.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let isLoggedIn = true;
  let router: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    getters = {
      isLoggedIn: () => isLoggedIn,
    };
    store = new Vuex.Store({ getters });
    router = new VueRouter();
  });

  it('renders not logged in message', () => {
    isLoggedIn = false;
    const wrapper = mount(Home, { localVue, vuetify, store, router, });
    expect(wrapper.text()).toContain('Not sure who you are');
    expect(wrapper.find('#login-msg a').attributes('href')).toBe('#/login');
  });
});





