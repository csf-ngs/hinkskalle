import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import { localVue } from '../setup';

import Users from '@/views/Users.vue';

describe('Users.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: any;
  let actions: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({});

    getters = {};
    actions = {};
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Users, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Users');
  });

});