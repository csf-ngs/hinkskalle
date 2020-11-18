import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import LatestContainers from '@/components/LatestContainers.vue';

import { localVue } from '../setup';
import { testLatestObj } from './container-store.spec';
import { Upload } from '@/store/models';

describe('LatestContainers.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let actions: any;
  let router: any;
  let latest: Upload[] = [];
  let mockLoadLatest: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [
        { name: 'ContainerDetails', path: '/:entity/:collection/:container' }
      ]
    });
    mockLoadLatest = jest.fn();
    getters = {
      'containers/latest': () => latest,
    };
    actions = {
      'containers/latest': mockLoadLatest,
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(LatestContainers, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Latest Uploads:');
    expect(mockLoadLatest).toHaveBeenCalledTimes(1);
  });

  it('renders uploads', () => {
    latest = testLatestObj;
    const wrapper = mount(LatestContainers, { localVue, vuetify, store, router });
    expect(wrapper.findAll('a.v-list-item')).toHaveLength(2);

  });
});