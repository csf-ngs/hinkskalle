import { mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import VueRouter from 'vue-router';

import GroupDetails from '@/views/GroupDetails.vue';
import { localVue } from '../setup';

import { makeTestGroupObj } from '../_data';

describe('GroupDetails.vue', () => {
  let vuetify: any;
  let router: VueRouter
  let store: Store<any>;

  let getters: any;
  let actions: any;
  let mutations: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();

    getters = {
      'groups/list': () => jest.fn(),
    };
    actions = {
      'groups/get': jest.fn(() => makeTestGroupObj()),
      'entities/get': jest.fn(),
    }
    mutations = {
      'snackbar/showError': jest.fn(),
    };

    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('render something', async () => {
    const wrapper = mount(GroupDetails, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Group Details');
    expect(actions['groups/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.group).not.toBeNull();
    expect(actions['entities/get']).toHaveBeenCalledTimes(1);
  });

  it('shows error on get container fail', async () => {
    actions['groups/get'].mockRejectedValue("fail");
    const wrapper = mount(GroupDetails, { localVue, vuetify, store, router });
    expect(actions['groups/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.error).toBe('fail');
  });

  it('shows error on get entity fail', async () => {
    actions['entities/get'].mockRejectedValue("fail");
    const wrapper = mount(GroupDetails, { localVue, vuetify, store, router });
    expect(actions['groups/get']).toHaveBeenCalledTimes(1);
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.error).toBe('fail');
  });

});