import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import LatestContainers from '@/components/LatestContainers.vue';

import { localVue } from '../setup';
import { makeTestLatestObj } from '../_data';
import { Upload } from '@/store/models';

describe('LatestContainers.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let actions: any;
  let router: any;
  let latest: Upload[] = [];

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [
        { name: 'ContainerDetails', path: '/:entity/:collection/:container' }
      ]
    });
    getters = {
      'containers/latest': () => latest,
    };
    actions = {
      'containers/latest': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(LatestContainers, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Latest Uploads');
    expect(actions['containers/latest']).toHaveBeenCalledTimes(1);
  });

  it('renders uploads', () => {
    latest = makeTestLatestObj();
    const wrapper = mount(LatestContainers, { localVue, vuetify, store, router });
    expect(wrapper.findAll('.v-card.upload')).toHaveLength(2);

  });
});