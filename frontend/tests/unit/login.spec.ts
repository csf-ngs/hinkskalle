import { mount, createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import Vue from 'vue';

import Login from '@/views/Login.vue';

import { localVue } from '../setup';

import { plainToConfigParams } from '@/store/models';

const configParams = plainToConfigParams({
  enable_register: true,
});

describe('Login.vue', () => {
  let store: any;
  let vuetify: any;
  let router: any;

  beforeEach(() => {
    store = new Vuex.Store({
      getters: {
        config: jest.fn().mockReturnValue(configParams),
      },
    });
    vuetify = new Vuetify();
    router = new VueRouter();
  });

  it('has title', () => {
    const wrapper = mount(Login, { localVue, store, vuetify, router });
    expect(wrapper.find('div.v-tab').text()).toBe('Login');
  });

  it('checks required', async () => {
    const wrapper = mount(Login, { localVue, store, vuetify, router });
    expect(wrapper.find('button#login').attributes('disabled')).toBeTruthy();

    await wrapper.find('input#username').setValue('oink');
    await wrapper.find('input#password').setValue('hase');

    await Vue.nextTick();
    expect(wrapper.find('button#login').attributes('disabled')).toBeFalsy();
  });

  it('routes on successful login', async () => {
    const myLocal = createLocalVue();
    myLocal.use(Vuex);

    const mockRouter = { push: jest.fn() };
    store = new Vuex.Store({
      getters: {
        config: jest.fn().mockReturnValue(configParams),
        currentUser: jest.fn().mockReturnValue({ isAdmin: false }),
      },
      actions: {
        requestAuth: jest.fn().mockResolvedValue('dummy'),
      }
    })
    const wrapper = mount(Login, { localVue: myLocal, store, vuetify, 
      mocks: { $router: mockRouter },
      data: () => ({ localState: { user: { username: 'oink', password: 'hase' }}})
    });
    
    await wrapper.find('form').trigger('submit');
    await Vue.nextTick();
    expect(mockRouter.push).toHaveBeenCalledWith('/');
  });

  it('shows error on failed login', async () => {
    store = new Vuex.Store({
      getters: {
        config: jest.fn().mockReturnValue(configParams),
      },
      actions: {
        requestAuth: jest.fn().mockRejectedValue({ message: 'dummy' }),
      }
    });
    const wrapper = mount(Login, { localVue, store, vuetify, router });
    await wrapper.find('form').trigger('submit');
    // not really elegant
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.find('div.v-alert').text()).toContain('dummy');
  });


});