import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import Collections from '@/views/Collections.vue';

import { localVue } from '../setup';

import { testCollectionsObj } from './collections-store.spec';
import {Collection} from '@/store/models';

describe('Collections.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: any;
  let actions: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();

    getters = {
      'collections/list': () => testCollectionsObj,
    };
    actions = {
      'collections/list': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Collections');
    expect(actions['collections/list']).toHaveBeenCalledTimes(1);
  });

  it('renders collections', () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#collections tbody tr')).toHaveLength(2);
  });

  it('searches collection names', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('esel');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections tbody tr')).toHaveLength(1);
    expect(wrapper.find('div#collections tbody tr').text()).toContain('esel');
    done();
  });

  it('searches collection descriptions', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('shawn');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections tbody tr')).toHaveLength(1);
    expect(wrapper.find('div#collections tbody tr').text()).toContain('schaf');
    done();
  });

  it('shows create dialog', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('button#create-collection').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('New Collection');
    expect(wrapper.vm.$data.localState.editItem.name).toBeUndefined();

    wrapper.find('input#name').setValue('tintifax');
    expect(wrapper.vm.$data.localState.editItem.name).toBe('tintifax');

    done();
  });

  it('clones edit item', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('div#collections tbody tr button.mdi-pencil').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.editItem.name).toBe(testCollectionsObj[0].name);
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();

    wrapper.find('input#name').setValue('tintifax');
    expect(wrapper.vm.$data.localState.editItem.name).toBe('tintifax');
    expect(wrapper.vm.$data.localState.editItem.name).not.toBe(testCollectionsObj[0].name);

    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('Edit Collection');

    done();
  });
});