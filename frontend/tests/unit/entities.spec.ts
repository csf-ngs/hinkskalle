import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import Entities from '@/views/Entities.vue';

import { localVue } from '../setup';

import { each as _each, cloneDeep as _cloneDeep } from 'lodash';
import {Entity, User} from '@/store/models';
import {makeTestEntitiesObj, makeTestUserObj} from '../_data';

let testUserObj: User;
let testEntitiesObj: Entity[];

beforeAll(() => {
  testUserObj = makeTestUserObj();
  testEntitiesObj = makeTestEntitiesObj();
  _each(testEntitiesObj, e => e.createdBy=testUserObj.username);
});

// needed to silence vuetify dialog warnings
document.body.setAttribute('data-app', 'true');

describe('Entities.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: { [key: string]: jest.Mock<any, any>};
  let mutations: { [key: string]: jest.Mock<any, any>};
  let actions: { [key: string]: jest.Mock<any, any>};

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [ { path: '/oink/:entity/oink', name: 'EntityCollections' } ]
    });

    mutations = {
      'users/setSearchResult': jest.fn(),
    };
    getters = {
      'entities/list': jest.fn().mockReturnValue(testEntitiesObj),
      'currentUser': jest.fn().mockReturnValue(testUserObj),
    };
    actions = {
      'entities/list': jest.fn(),
      'users/search': jest.fn(),
    };
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', () => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Entities');
    expect(actions['entities/list']).toHaveBeenCalledTimes(1);
  });

  it('renders entities', () => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#entities .entity')).toHaveLength(2);
  });

  it('searches entity names', async done => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('esel');
    await Vue.nextTick();
    expect(wrapper.findAll('div#entities .entity')).toHaveLength(1);
    expect(wrapper.find('div#entities .entity').text()).toContain('esel');
    done();
  });

  it('searches entity descriptions', async done => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    wrapper.find('input#search').setValue('shawn');
    await Vue.nextTick();
    expect(wrapper.findAll('div#entities .entity')).toHaveLength(1);
    expect(wrapper.find('div#entities .entity').text()).toContain('shawn');
    done();
  });

  it('shows create dialog', async done => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    testUserObj.isAdmin = true;
    await Vue.nextTick();
    wrapper.find('button#create-entity').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('New Entity');
    expect(wrapper.vm.$data.localState.editItem.name).toBeUndefined();

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeFalsy();

    done();
  });

  it('shows edit dialog', async done => {
    const wrapper = mount(Entities, { localVue, vuetify, store, router });
    wrapper.find('div#entities .entity button.mdi-pencil').trigger('click');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.editItem.name).toBe(testEntitiesObj[0].name);
    expect(wrapper.vm.$data.localState.showEdit).toBeTruthy();
    expect(wrapper.find('div.v-dialog.v-dialog--active div.headline').text()).toBe('Edit Entity');

    expect(wrapper.find('div#name input').attributes()['readonly']).toBeTruthy();

    done();
  });
});