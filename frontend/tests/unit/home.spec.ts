import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import Home from '@/views/Home.vue';

import { localVue } from '../setup';
import { plainToConfigParams } from '@/store/models';

describe('Home.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let actions: any;
  let isLoggedIn = true;
  let router: any;

  const config = plainToConfigParams({
    singularity_flavor: 'singularity',
  });

  const OLDENV = process.env;
  beforeEach(() => {
    process.env = { ...OLDENV  };
    process.env['VUE_APP_BACKEND_URL']='http://testha.se/'
    vuetify = new Vuetify();
    getters = {
      config: () => jest.fn().mockReturnValue(config),
      isLoggedIn: () => isLoggedIn,
      currentUser: () => jest.fn().mockReturnValue({ username: 'test.hase' }),
    };
    actions = {
      'containers/latest': jest.fn(),
      'users/getStarred': jest.fn(),
    }
    store = new Vuex.Store({ getters, actions });
    router = new VueRouter();
  });
  afterAll(() => {
    process.env = OLDENV;
  });

  it('renders not logged in message', () => {
    isLoggedIn = false;
    const wrapper = mount(Home, { localVue, vuetify, store, router, });
    expect(wrapper.text()).toContain('Not sure who you are');
    expect(wrapper.find('#login-msg a').attributes('href')).toBe('#/login');
  });


  it('renders latest containers when logged in', () => {
    isLoggedIn = true;
    const wrapper = mount(Home, { localVue, vuetify, store, router, });
    expect(wrapper.find('latest-containers')).not.toBeNull();
  });
  it('renders starred containers when logged in', () => {
    isLoggedIn = true;
    const wrapper = mount(Home, { localVue, vuetify, store, router, });
    expect(wrapper.find('starred-containers')).not.toBeNull();
  });
});





