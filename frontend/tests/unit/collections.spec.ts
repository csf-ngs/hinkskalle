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
  testEntityObj.createdBy = testUserObj.username;
});


// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');


describe('Collections.vue', () => {
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
        { name: 'Containers', path: '/:entity/:collection' },
      ]
    });

    getters = {
      'collections/list': () => testCollectionsObj,
      'collections/currentEntity': () => testEntityObj,
      'currentUser': () => testUserObj,
    };
    mutations = {
      'snackbar/showSuccess': jest.fn(),
      'snackbar/showError': jest.fn(),
    };
    actions = {
      'collections/list': jest.fn(),
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

  it('searches collection names', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('esel');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections .collection')).toHaveLength(1);
    expect(wrapper.find('div#collections .collection').text()).toContain('esel');
    done();
  });

  it('searches collection descriptions', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('shawn');
    await Vue.nextTick();
    expect(wrapper.findAll('div#collections .collection')).toHaveLength(1);
    expect(wrapper.find('div#collections .collection').text()).toContain('schaf');
    done();
  });

  it('shows create dialog', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('button#create-collection').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('New Collection');
    expect(wrapper.vm.$data.localState.editItem.name).toBeUndefined();

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeFalsy();
    done();
  });

  it('shows edit dialog', async done => {
    const wrapper = mount(Collections, { localVue, vuetify, store, router });
    wrapper.find('div#collections .collection button.mdi-pencil').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.editItem.name).toBe(testCollectionsObj[0].name);
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('Edit Collection');

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeTruthy();

    done();
  });

  it('uses route params for default entity name', async done => {
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
    await Vue.nextTick();
    wrapper.find('button#save').trigger('click');
    expect(actions['collections/create']).toHaveBeenLastCalledWith(expect.anything(), expectCollection);
    
    done();
  });
});