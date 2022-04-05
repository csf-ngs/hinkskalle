import { mount } from '@vue/test-utils';
import Vue from 'vue';
import Vuetify from 'vuetify';
import Vuex, { Store } from 'vuex';
import { localVue } from '../setup';

import { Container } from '@/store/models';
import ContainerStars from '@/components/ContainerStars.vue';

import { makeTestContainersObj } from '../_data';

describe('ContainerStars.vue', () => {
  let testContainersObj: Container[];
  let vuetify: any;
  let store: Store<any>;

  let getters: any;
  let actions: any;

  beforeEach(() => {
    testContainersObj = makeTestContainersObj();
    vuetify = new Vuetify();
    getters = {
      'users/starred': () => [ testContainersObj[0] ],
    };
    actions = {
      'users/addStar': jest.fn().mockResolvedValue({}),
      'users/removeStar': jest.fn().mockResolvedValue({}),
      'users/getStarred': jest.fn().mockResolvedValue({}),
    }
    store = new Vuex.Store({ getters, actions });
  });

  it('enables stars', () => {
    const propsData = {
      container: testContainersObj[0]
    };
    const wrapper = mount(ContainerStars, { localVue, vuetify, store, propsData });
    expect((wrapper.vm as any).isStarred()).toBeTruthy();
  });
  it('enables stars', () => {
    const propsData = {
      container: testContainersObj[1]
    };
    const wrapper = mount(ContainerStars, { localVue, vuetify, store, propsData });
    expect((wrapper.vm as any).isStarred()).toBeFalsy();
  });

  it('calls addStar', async () => {
    const propsData = {
      container: testContainersObj[1]
    };
    const wrapper = mount(ContainerStars, { localVue, vuetify, store, propsData });
    wrapper.find('button').trigger('click');
    await Vue.nextTick();
    expect(actions['users/addStar']).toHaveBeenLastCalledWith(expect.anything(), testContainersObj[1]);
    await Vue.nextTick();
    expect(wrapper.find('.v-badge__badge').text()).toBe("1");
  });
  it('calls removeStar', async () => {
    testContainersObj[0].stars=1;
    const propsData = {
      container: testContainersObj[0]
    };
    const wrapper = mount(ContainerStars, { localVue, vuetify, store, propsData });
    wrapper.find('button').trigger('click');
    await Vue.nextTick();
    expect(actions['users/removeStar']).toHaveBeenLastCalledWith(expect.anything(), testContainersObj[0]);
    await Vue.nextTick();
    expect(wrapper.find('.v-badge__badge').text()).toBe("0");
  });
});