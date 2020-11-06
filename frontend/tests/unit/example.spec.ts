import { shallowMount } from '@vue/test-utils'
import Vuetify from 'vuetify';

import HelloWorld from '@/components/HelloWorld.vue'

import { localVue } from '../setup';

describe('HelloWorld.vue', () => {
  let vuetify: any;
  beforeEach(() => {
    vuetify = new Vuetify();
  });

  it('renders props.msg when passed', () => {
    const msg = ''
    const wrapper = shallowMount(HelloWorld, {
      localVue,
      vuetify,
      propsData: { msg }
    })
    expect(wrapper.text()).toMatch(msg)
  })
})
