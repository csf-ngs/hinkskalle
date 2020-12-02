import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import { localVue } from '../setup';

import Users from '@/views/Users.vue';
import { makeTestUserObj } from '../_data';

describe('Users.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: { [name: string]: jest.Mock<any, any>};
  let actions: { [name: string]: jest.Mock<any, any>};

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({});

    getters = {
      'users/list': jest.fn(),
    };
    actions = {
      'users/list': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Users, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Users');
    expect(actions['users/list']).toHaveBeenCalled();
  });

  it('renders user rows', () => {
    const testUsers = [ makeTestUserObj(), makeTestUserObj() ];
    testUsers[1].id="2";
    getters['users/list'].mockReturnValue(testUsers);
    const wrapper = mount(Users, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#users tbody tr')).toHaveLength(2);
  });

  it('checks password matching', ()=> {
    const wrapper = mount(Users, { localVue, vuetify, store, router });
    expect((wrapper.vm as any).passwordsMatching).toBeTruthy();
    wrapper.setData({ localState: { password1: 'eins', password2: 'eins' } });
    expect((wrapper.vm as any).passwordsMatching).toBeTruthy();
    wrapper.setData({ localState: { password1: 'eins', password2: 'zwei' } });
    expect((wrapper.vm as any).passwordsMatching).toBeFalsy();

  });

});