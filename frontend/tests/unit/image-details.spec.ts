import { mount } from '@vue/test-utils';


import Vuetify from 'vuetify';
import Vuex from 'vuex';
import VueRouter from 'vue-router';

import ImageDetails from '@/components/ImageDetails.vue';

import { localVue } from '../setup';
import { testImagesObj } from './images-store.spec';
import Vue from 'vue';

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
    const propsData = { image: testImagesObj[0] };
    const wrapper = mount(ImageDetails, { localVue, vuetify, store, router, propsData });
    expect(wrapper.find('button.v-expansion-panel-header .v-chip').text()).toContain('latest');
  });

  it('renders tag chips', () => {
    const propsData = { image: testImagesObj[0] };
    const wrapper = mount(ImageDetails, { localVue, vuetify, store, router, propsData });
    expect(wrapper.findAll('button.v-expansion-panel-header .v-chip')).toHaveLength(2);
  });


});