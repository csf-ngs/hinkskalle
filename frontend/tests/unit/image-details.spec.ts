import { mount } from '@vue/test-utils';


import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import ImageDetails from '@/components/ImageDetails.vue';

import { localVue } from '../setup';
import { testImagesObj } from './images-store.spec';

describe('LatestContainers.vue', () => {
  let vuetify: any;
  let store: any;
  let router: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    router = new VueRouter();
    store = new Vuex.Store({});
  });

  it('renders something', () => {
    const wrapper = mount(ImageDetails, { localVue, vuetify, store, router });
    wrapper.setProps({ image: testImagesObj[0] });
    expect(wrapper.text()).toBe('');
  });
});