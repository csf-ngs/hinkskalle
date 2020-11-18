import { mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import VueRouter from 'vue-router';

import Containers from '@/views/Containers.vue';

import { localVue, localVueNoRouter } from '../setup';

import { testContainersObj } from './container-store.spec';
import {Container} from '@/store/models';

// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');

describe('Containers.vue', () => {
  let vuetify: any;
  let store: Store<any>;
  let router: VueRouter;

  let getters: any;
  let actions: any;
  let mutations: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [
        { name: 'ContainerDetails', path: '/:entity/:collection/:container' }
      ]
    });

    getters = {
      'containers/list': () => testContainersObj,
    };
    mutations = {
      'snackbar/showSuccess': jest.fn(),
      'snackbar/showError': jest.fn(),
    };
    actions = {
      'containers/list': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Containers');
    expect(actions['containers/list']).toHaveBeenCalledTimes(1);
  });

  it('passes route params to container list', () => {
    const $route = {
      path: '/something', params: { entity: 'testgiraffe', collection: 'testcapybara' }
    }
    const wrapper = mount(Containers, { localVue: localVueNoRouter, vuetify, store, router, mocks: { $route }, stubs: [ 'router-link' ] });
    expect(actions['containers/list']).toHaveBeenLastCalledWith(expect.anything(), { entity: $route.params.entity, collection: $route.params.collection });
  });

  it('renders containers', () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#containers .container')).toHaveLength(2);
  });

  it('searches container names', async done => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('zebra');
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container')).toHaveLength(1);
    expect(wrapper.find('div#containers .container').text()).toContain('testzebra');
    done();
  });

  it('searches container descriptions', async done => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('Nilpf');
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container')).toHaveLength(1);
    expect(wrapper.find('div#containers .container').text()).toContain('testhippo');
    done();
  });
});