import { shallowMount, mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';

import App from '@/App.vue';

import { localVue } from '../setup';

describe('App.vue', () => {
  let getters: any;
  let mutations: any;
  let actions: any;
  let store: any;
  let vuetify: any;
  let router: any;

  let isLoggedIn = true;
  let showSnackbar = false;

  beforeEach(() => {
    mutations = {
      'registerInterceptor': jest.fn(),
      'snackbar/close': jest.fn(),
    };
    getters = {
      isLoggedIn: () => isLoggedIn,
      currentUser: jest.fn().mockReturnValue({ fullname: 'Test Hase' }),
      'snackbar/show': () => showSnackbar,
      'snackbar/msg': () => '',
      'adm/ldapStatus': jest.fn(),
    };
    actions = {
      'adm/ldapStatus': jest.fn(),
    };
    store = new Vuex.Store({ getters, mutations, actions });
    vuetify = new Vuetify();
    router = new VueRouter();
  });

  it('has title', () => {
    const wrapper = shallowMount(App, { localVue, store, vuetify });
    expect(wrapper.text()).toContain('Hinkskalle');
    expect(mutations.registerInterceptor).toHaveBeenCalled();
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
    expect(mutations['snackbar/close']).toHaveBeenCalled();
  });

  it('can hide the snackbar via computed prop', () => {
    showSnackbar = true;
    const wrapper = mount(App, { localVue, store, vuetify, router });
    wrapper.setData({ showSnackbar: false });
    expect(mutations['snackbar/close']).toHaveBeenCalled();
  });

  it('does not render user admin item', () => {
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(wrapper.findAll('a#user-admin').length).toBe(0);
  });
  it('renders user admin item for admins', () => {
    getters['currentUser'].mockReturnValue({
      fullname: 'Test Hase',
      isAdmin: true,
    }); 
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(wrapper.findAll('a#user-admin').length).toBe(1);
  });

  it('does not call get ldap status', () => {
    isLoggedIn = false;
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(actions['adm/ldapStatus']).not.toHaveBeenCalled();
  });
  it('does not call get ldap status', () => {
    isLoggedIn = true;
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(actions['adm/ldapStatus']).not.toHaveBeenCalled();
  });
  it('does call get ldap status for admins', () => {
    isLoggedIn = true;
    getters['currentUser'] = jest.fn().mockReturnValue({ fullname: 'Test Hase' });
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(actions['adm/ldapStatus']).not.toHaveBeenCalled();
  });
  it('renders ldap menu item', () => {
    getters['adm/ldapStatus'].mockReturnValue({
      status: 'configured',
    });
    getters['currentUser'].mockReturnValue({
      fullname: 'Test Hase',
      isAdmin: true,
    });
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(wrapper.find('a#ldap-admin .v-list-item__content').text()).toMatch('LDAP Administration');
  });
  it('does not render ldap menu item when disabled', () => {
    getters['adm/ldapStatus'].mockReturnValue({
      status: 'disabled',
    });
    getters['currentUser'].mockReturnValue({
      fullname: 'Test Hase',
      isAdmin: true,
    });
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(wrapper.findAll('a#ldap-admin').length).toBe(0);
  });
  it('does not render ldap menu item when null value', () => {
    getters['adm/ldapStatus'].mockReturnValue(null);
    getters['currentUser'].mockReturnValue({
      fullname: 'Test Hase',
      isAdmin: true,
    });
    const wrapper = mount(App, { localVue, store, vuetify, router });
    expect(wrapper.findAll('a#ldap-admin').length).toBe(0);
  });
});