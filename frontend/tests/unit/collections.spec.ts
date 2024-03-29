import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';


import Collections from '@/views/Collections.vue';

import { localVue, localVueNoRouter } from '../setup';

import {Collection, Entity, User} from '@/store/models';

import { makeTestCollectionsObj, makeTestUserObj } from '../_data';

import { cloneDeep as _cloneDeep, each as _each } from 'lodash';

let testUserObj: User;
let testCollectionsObj: Collection[];
let testEntityObj: Entity;

beforeAll(() => {
  testUserObj = makeTestUserObj();
  testCollectionsObj = makeTestCollectionsObj();
  _each(testCollectionsObj, c => c.createdBy = testUserObj.username );

  testEntityObj = new Entity();
  testEntityObj.canEdit = true;
  testEntityObj.createdBy = testUserObj.username;
});


// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');


describe('Collections.vue', () => {
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
        { name: 'Containers', path: '/:entity/:collection' },
      ]
    });

    getters = {
      'collections/list': jest.fn().mockReturnValue(testCollectionsObj),
      'collections/currentEntity': jest.fn().mockReturnValue(testEntityObj),
      'currentUser': jest.fn().mockReturnValue(testUserObj),
    };
    mutations = {
      'snackbar/showSuccess': jest.fn(),
      'snackbar/showError': jest.fn(),
    };
    actions = {
      'collections/list': jest.fn(),
      'users/search': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Collections');
    expect(actions['collections/list']).toHaveBeenCalledTimes(1);
  });

  it('renders collections', () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#collections .collection')).toHaveLength(2);
  });

  it('searches collection names', async () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('esel');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections .collection')).toHaveLength(1);
    expect(wrapper.find('div#collections .collection').text()).toContain('esel');
  });

  it('searches collection descriptions', async () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('shawn');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections .collection')).toHaveLength(1);
    expect(wrapper.find('div#collections .collection').text()).toContain('schaf');
  });

  it('shows create dialog', async () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('button#create-collection').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('New Collection');
    expect(wrapper.vm.$data.localState.editItem.name).toBeUndefined();

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeFalsy();
  });

  it('shows edit dialog', async () => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('div#collections .collection button.mdi-pencil').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.editItem.name).toBe(testCollectionsObj[0].name);
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('Edit Collection');

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeTruthy();

  });

  it.skip('uses route params for default entity name', async () => {
    const $route = {
      path: '/test', params: { entity: 'oinkhase' }
    };
    actions['collections/create']=jest.fn();
    store = new Vuex.Store({ getters, actions, mutations });
    const expectCollection = new Collection();
    expectCollection.name='tintifax';
    expectCollection.description='tintifax';
    expectCollection.createdAt=expect.anything();
    expectCollection.entityName=$route.params.entity;

    const wrapper = mount(Collections, { localVue: localVueNoRouter, vuetify, store, router, stubs: ['router-link'], mocks: { $route } });
    expect(actions['collections/list']).toHaveBeenLastCalledWith(expect.anything(), $route.params.entity);
    wrapper.find('button#create-collection').trigger('click');
    await Vue.nextTick();
    wrapper.setData({ localState: { editItem: {
      name: expectCollection.name,
      description: expectCollection.description,
    }}});
    await Vue.nextTick();
    await wrapper.find('button#save').trigger('click');
    expect(actions['collections/create']).toHaveBeenLastCalledWith(expect.anything(), expectCollection);
    
  });
});