
import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import { localVue } from '../setup';

import Ldap from '@/views/Ldap.vue';

describe('Ldap.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;
  let actions: any;
  let getters: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();

    getters = {
      'adm/ldapStatus': jest.fn(),
    };
    actions = {
      'adm/ldapStatus': jest.fn(),
    };

    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Ldap, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('LDAP Administration');
    expect(actions['adm/ldapStatus']).toHaveBeenCalled();
  });
});