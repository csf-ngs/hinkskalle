import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';

import LatestContainers from '@/components/LatestContainers.vue';

import { localVue } from '../setup';

describe('LatestContainers.vue', () => {
  let vuetify: any;

  beforeEach(() => {
    vuetify = new Vuetify();
  });

  it('renders something', () => {
    const wrapper = mount(LatestContainers, { localVue, vuetify });
    expect(wrapper.text()).toContain('oink');
  });
});