import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';

import Tokens from '@/views/Tokens.vue';

import { localVue } from '../setup';
import { testTokenObj } from './token-store.spec';
import { Token } from '@/store/models';
import VueRouter from 'vue-router';

describe('Tokens.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let actions: any;
  let router: VueRouter;

  let tokens: Token[] = [];
  let mockLoadTokens: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    mockLoadTokens = jest.fn();
    router = new VueRouter();
    getters = {
      'tokens/tokens': () => tokens,
    };
    actions = {
      'tokens/list': mockLoadTokens,
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Tokens, { localVue, vuetify, store, router });
    expect(wrapper.text()).toContain('Tokens');
    expect(mockLoadTokens).toHaveBeenCalledTimes(1);
  });

  it('renders tokens', () => {
    tokens = testTokenObj;
    const wrapper = mount(Tokens, { localVue, vuetify, store, router });
    expect(wrapper.findAll('div#tokens tbody tr')).toHaveLength(2);
  });
});