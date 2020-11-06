import { shallowMount, mount } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';

import Login from '@/views/Login.vue';

import { localVue } from '../setup';

describe('Login.vue', () => {
  let store: any;
  let vuetify: any;
  let router: any;

  beforeEach(() => {
    store = new Vuex.Store({});
    vuetify = new Vuetify();
    router = new VueRouter();
  });

  it('has title', () => {
    const wrapper = mount(Login, { localVue, store, vuetify, router });
    expect(wrapper.find('h4').text()).toBe('Login');
  });

  it('checks required', async () => {
    const wrapper = mount(Login, { localVue, store, vuetify, router });
    expect(wrapper.find('button#login').attributes('disabled')).toBeTruthy();

    await wrapper.setData({
      state: {
        user: {
          username: 'oink',
          password: 'hase',
        }
      }
    });

    expect(wrapper.find('button#login').attributes('disabled')).toBeFalsy();

  });



});