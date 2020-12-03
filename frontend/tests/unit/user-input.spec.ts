import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';

import UserInput from '@/components/UserInput.vue';

import { localVue } from '../setup';
import Vue from 'vue';

describe("UserInput.vue", () => {
  let vuetify: any;
  let store: any;
  let getters: { [key: string]: jest.Mock<any, any>};
  let mutations: { [key: string]: jest.Mock<any, any>};
  let actions: { [key: string]: jest.Mock<any, any>};

  beforeEach(() => {
    vuetify = new Vuetify();
    getters = {
      'users/searchResult': jest.fn(),
    }
    mutations = {
      'users/setSearchResult': jest.fn(),
    };
    actions = {
      'users/search': jest.fn(),
    };
    store = new Vuex.Store({ mutations, actions, getters });
  });

  it('renders something', () => {
    const propsData = { value: 'test.oink' };
    const wrapper = mount(UserInput, { localVue, vuetify, store, propsData });
    expect(wrapper.find('label').text()).toBe('Username');
  });

  it('sets initial search value', async done => {
    const propsData = { value: 'test.oink' };
    const wrapper = mount(UserInput, { localVue, vuetify, store, propsData });
    await Vue.nextTick();
    expect(actions['users/search']).toHaveBeenLastCalledWith(expect.anything(), { username: 'test.oink' });
    expect(wrapper.find('input').attributes()['readonly']).toBeFalsy();
    done();
  });

  it('sets readonly', async done => {
    const propsData = { value: 'test.oink', readonly: true };
    const wrapper = mount(UserInput, { localVue, vuetify, store, propsData });
    expect(wrapper.find('input').attributes()['readonly']).toBeTruthy();
    done();

  });

});