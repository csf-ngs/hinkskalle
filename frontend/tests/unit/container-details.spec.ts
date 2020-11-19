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
      'containers/get': jest.fn(() => testContainersObj[0]),
      'images/list': jest.fn(() => []), 
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', async done => {
    const wrapper = mount(ContainerDetails, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Container Details');
    expect(actions['containers/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    expect(actions['images/list']).toHaveBeenCalledTimes(1);
    done();
  });

  it('shows error on get container fail', async done => {
    actions['containers/get'].mockRejectedValue("fail");
    const wrapper = mount(ContainerDetails, { localVue, vuetify, store, router });
    expect(actions['containers/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(mutations['snackbar/showError']).toHaveBeenCalledWith(expect.anything(), "fail");
    done();
  });

  it('shows error on get images fail', async done => {
    actions['images/list'].mockRejectedValue("fail");
    const wrapper = mount(ContainerDetails, { localVue, vuetify, store, router });
    expect(actions['containers/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(mutations['snackbar/showError']).toHaveBeenCalledWith(expect.anything(), "fail");
    done();
  });
});