import { mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import VueRouter from 'vue-router';

import Containers from '@/views/Containers.vue';

import { localVue, localVueNoRouter } from '../setup';

import { clone as _clone } from 'lodash';

import { makeTestCollectionsObj, makeTestContainersObj } from '../_data';
import {Collection, Container} from '@/store/models';

// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');

let testContainersObj: Container[];
let testCollection: Collection;
beforeAll(() => {
  testContainersObj = makeTestContainersObj();
  testCollection = makeTestCollectionsObj()[0];
})


describe('Containers.vue', () => {
  let vuetify: any;
  let store: Store<any>;
  let router: VueRouter;

  let getters: { [key: string]: jest.Mock<any, any>};
  let actions: { [key: string]: jest.Mock<any, any>};
  let mutations: { [key: string]: jest.Mock<any, any>};

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [
        { name: 'ContainerDetails', path: '/:entity/:collection/:container' }
      ]
    });

    getters = {
      'containers/list': jest.fn().mockReturnValue(testContainersObj),
      'containers/currentCollection': jest.fn().mockReturnValue(testCollection),
      'users/starred': jest.fn().mockReturnValue([ testContainersObj[0] ]),
    };
    mutations = {
      'snackbar/showSuccess': jest.fn(),
      'snackbar/showError': jest.fn(),
    };
    actions = {
      'containers/list': jest.fn().mockResolvedValue('any'),
      'users/getStarred': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', async () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Containers');
    await Vue.nextTick();
    await Vue.nextTick();
    expect(actions['containers/list']).toHaveBeenCalledTimes(1);
    expect(actions['users/getStarred']).toHaveBeenCalledTimes(2);
  });

  it('passes route params to container list', async () => {
    const $route = {
      path: '/something', params: { entity: 'testgiraffe', collection: 'testcapybara' }
    }
    const wrapper = mount(Containers, { localVue: localVueNoRouter, vuetify, store, router, mocks: { $route }, stubs: [ 'router-link' ] });
    await Vue.nextTick();
    await Vue.nextTick();
    expect(actions['containers/list']).toHaveBeenLastCalledWith(expect.anything(), expect.objectContaining({ entityName: $route.params.entity, collectionName: $route.params.collection }));
  });

  it('renders containers', async () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container')).toHaveLength(2);
  });

  it('renders container types', async () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container i.mdi-folder-multiple')).toHaveLength(1);
  });


  it('searches container names', async () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    await Vue.nextTick();
    await Vue.nextTick();
    wrapper.find('input#search').setValue('zebra');
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container')).toHaveLength(1);
    expect(wrapper.find('div#containers .container').text()).toContain('testzebra');
  });

  it('searches container descriptions', async () => {
    const wrapper = mount(Containers, { localVue, vuetify, store, router });
    await Vue.nextTick();
    await Vue.nextTick();
    wrapper.find('input#search').setValue('Nilpf');
    await Vue.nextTick();
    expect(wrapper.findAll('div#containers .container')).toHaveLength(1);
    expect(wrapper.find('div#containers .container').text()).toContain('testhippo');
  });
});