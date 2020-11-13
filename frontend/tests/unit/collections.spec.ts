import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import Collections from '@/views/Collections.vue';

import { localVue } from '../setup';

describe('Collections.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();
    store = new Vuex.Store({});
  });

  it('renders something', () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Collections');
  });
});