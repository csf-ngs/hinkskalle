import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';

import Tokens from '@/views/Tokens.vue';

import { localVue } from '../setup';
import { testTokenObj } from './token-store.spec';
import { Token } from '@/store/models';

describe('Tokens.vue', () => {
  let vuetify: any;
  let store: any;
  let getters: any;
  let actions: any;

  let tokens: Token[] = [];
  let mockLoadTokens: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    mockLoadTokens = jest.fn();
    getters = {
      'tokens/tokens': () => tokens,
    };
    actions = {
      'tokens/list': mockLoadTokens,
    };
    store = new Vuex.Store({ getters, actions });
  });

  it('renders something', () => {
    const wrapper = mount(Tokens, { localVue, vuetify, store });
    expect(wrapper.text()).toContain('Tokens');
    expect(mockLoadTokens).toHaveBeenCalledTimes(1);
  });

  it('renders tokens', () => {
    tokens = testTokenObj;
    const wrapper = mount(Tokens, { localVue, vuetify, store });
    expect(wrapper.findAll('div#tokens tbody tr')).toHaveLength(2);
  });
});