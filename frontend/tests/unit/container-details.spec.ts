import { mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import VueRouter from 'vue-router';

import ContainerDetails from '@/views/ContainerDetails.vue';

import { localVue, localVueNoRouter } from '../setup';

import { testContainersObj } from './container-store.spec';
import {Container} from '@/store/models';

// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');

describe('ContainerDetails.vue', () => {
  let vuetify: any;
  let store: Store<any>;
  let router: VueRouter;

  let getters: any;
  let actions: any;
  let mutations: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();

    getters = {
      'containers/list': () => testContainersObj,
    };
    mutations = {
      'snackbar/showSuccess': jest.fn(),
      'snackbar/showError': jest.fn(),
    };
    actions = {
      'containers/get': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', () => {
    const wrapper = mount(ContainerDetails, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Container Details');
    expect(actions['containers/get']).toHaveBeenCalledTimes(1);
  });
});