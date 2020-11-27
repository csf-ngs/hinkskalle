import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import StarredContainers from '@/components/StarredContainers.vue';

import { localVue } from '../setup';
import { makeTestContainersObj } from '../_data';

describe('StarredContainers.vue', () => {
  let vuetify: Vuetify;
  let store: any;
  let router: VueRouter;
  let getters: any;
  let actions: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    getters = {
      'users/starred': () => makeTestContainersObj(),
    };
    actions = {
      'users/getStarred': jest.fn(),
    };
    store = new Vuex.Store({ actions, getters });
    router = new VueRouter({
      routes: [
        { name: 'ContainerDetails', path: '/:entity/:collection/:container' }
      ]
    });
  });

  it('renders something', () => {
    const wrapper = mount(StarredContainers, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Starred Containers');
    expect(actions['users/getStarred']).toHaveBeenCalledTimes(1);
  });

  it('renders containers', () => {
    const wrapper = mount(StarredContainers, { localVue, vuetify, store, router });
    expect(wrapper.findAll('.v-card.x-container')).toHaveLength(2);

  });
})
