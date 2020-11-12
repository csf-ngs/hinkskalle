import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';

import Account from '@/views/Account.vue';

import { localVue } from '../setup';

import { testUserObj } from './store.spec';

describe('Account.vue', () => {
  let vuetify: any;
  let store: any;

  let getters: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    getters = {
      currentUser: () => testUserObj,
    };
    store = new Vuex.Store({ getters });

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
});