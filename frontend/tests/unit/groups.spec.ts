import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import VueRouter from 'vue-router';

import Groups from '@/views/Groups.vue';

import { localVue } from '../setup';

import {Group, GroupMember, GroupRoles, User} from '@/store/models';
import {makeTestGroupObj, makeTestUserObj} from '../_data';

describe('Groups.vue', () => {
  let vuetify: any;
  let store: any;
  let router: VueRouter;

  let getters: { [key: string]: jest.Mock<any, any>};
  let mutations: { [key: string]: jest.Mock<any, any>};
  let actions: { [key: string]: jest.Mock<any, any>};

  let testGroupObj: Group;
  let testUserObj: User;

  beforeAll(() => {
    testGroupObj = makeTestGroupObj();
    testUserObj = makeTestUserObj();

    testGroupObj.users = [];
  })

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter({
      routes: [ 
        { path: '/groups/:group', name: 'GroupDetails' },
        { path: '/entity/:entity', name: 'EntityCollections' },
      ]
    });
    mutations = {}
    getters = {
      'groups/list': jest.fn(() => [ testGroupObj ]),
      'currentUser': jest.fn(() => testUserObj),
    }
    actions = {
      'groups/list': jest.fn(),
    }
    store = new Vuex.Store({ getters, actions, mutations });
  });

  it('renders something', () => {
    const wrapper = mount(Groups, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Groups');
    expect(actions['groups/list']).toHaveBeenCalledTimes(1);
  });


});