import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import Account from '@/views/Account.vue';

import { localVue } from '../setup';

import { testUserObj } from './store.spec';
import {User} from '@/store/models';

describe('Account.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: any;
  let actions: any;
  let mutations: any;
  let mockUpdateUser: jest.Mock<any, any>;
  let mockDeleteUser: jest.Mock<any, any>;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();
    mockUpdateUser = jest.fn();
    mockDeleteUser = jest.fn();
    getters = {
      currentUser: () => testUserObj,
    };
    mutations = {
      setUser: jest.fn(),
      logout: jest.fn(),
      'snackbar/showSuccess': jest.fn(),
    };
    actions = {
      'users/update': mockUpdateUser,
      'users/delete': mockDeleteUser,
    };
    store = new Vuex.Store({ getters, actions, mutations });
    router = new VueRouter();

  });

  it('renders something', done => {
    const wrapper = mount(Account, { localVue, vuetify, store });
    expect(wrapper.text()).toContain('Account');
    wrapper.vm.$nextTick(() => {
      expect((wrapper.find("input#firstname").element as HTMLInputElement).value)
        .toBe(testUserObj.firstname);
      done();
    });
  });

  it('clones currentUser', () => {
    const wrapper = mount(Account, { localVue, store, vuetify });
    expect(wrapper.vm.$data.localState.editUser.firstname).toBe(testUserObj.firstname);

    wrapper.setData({ localState: { editUser: { firstname: 'Oink' }}});
    expect(wrapper.vm.$data.localState.editUser.firstname).not.toBe(testUserObj.firstname);
  });

  it('can reset editUser', done => {
    const wrapper = mount(Account, { localVue, store, vuetify });
    wrapper.vm.$nextTick(() => {
      wrapper.find('input#firstname').setValue('Oink');
      expect(wrapper.vm.$data.localState.editUser.firstname).not.toBe(testUserObj.firstname);
      wrapper.find('button[type="reset"]').trigger('click');
      expect(wrapper.vm.$data.localState.editUser.firstname).toBe(testUserObj.firstname);
      done();
    });
  });

  it('saves user', async done => {
    const wrapper = mount(Account, { localVue, store, vuetify });
    await Vue.nextTick();

    wrapper.find("input#firstname").setValue('Oink');
    wrapper.find('button[type="submit"]').trigger('click');
    mockUpdateUser.mockResolvedValue(wrapper.vm.$data.localState.editUser);
    expect(mockUpdateUser).toHaveBeenCalledWith(expect.anything(), wrapper.vm.$data.localState.editUser);

    await Vue.nextTick();
    await Vue.nextTick();
    expect(mutations['snackbar/showSuccess']).toBeCalled();
    done();
  });

  /*
  it('deletes user', async (done) => {
    const wrapper = mount(Account, { localVue, store, vuetify, router });
    await Vue.nextTick();
    wrapper.find('button#delete').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.confirmDelete).toBeTruthy();
    wrapper.find('button#do-delete').trigger('click');
    expect(mockDeleteUser).toBeCalledWith(expect.anything(), wrapper.vm.$data.localState.editUser);
    await Vue.nextTick();
    await Vue.nextTick();
    expect(mutations.logout).toBeCalled();
    
    done();
  });
  */
});