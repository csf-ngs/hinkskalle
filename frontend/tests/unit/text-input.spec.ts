import { mount } from '@vue/test-utils';

import Vuetify from 'vuetify';
import Vuex from 'vuex';

import TextInput from '@/components/TextInput.vue';

import { localVue } from '../setup';
import Vue from 'vue';

const allTypes = ['text', 'textarea', 'yesno'];

describe('TextInput.vue', () => {
  let vuetify: any;
  let store: any;
  let mutations: any;
  let actions: any;

  beforeEach(() => {
    vuetify = new Vuetify();
    mutations = {
      'snackbar/showError': jest.fn(),
    }
    actions = {
      'testHase': jest.fn(),
    };
    store = new Vuex.Store({ mutations, actions });
  });

  it('renders something', () => {
    const propsData = {
      label: 'Testhase',
      staticValue: 'Squeak'
    };
    const wrapper = mount(TextInput, { localVue, vuetify, store, propsData, attrs: { id: 'oink' } });
    expect(wrapper.find('label').text()).toBe('Testhase');
    expect(wrapper.findAll('div#oink input')).toHaveLength(1);
  });

  allTypes.forEach(type => {
    it('can render '+type, () => {
      const propsData = {
        label: 'Testhase',
        staticValue: 'Squeak',
        type: type,
      };
      const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
      expect(wrapper.find('label').text()).toBe('Testhase');

    });
  });

  it('has static value', async done => {
    const propsData = {
      label: 'Testhase',
      staticValue: 'Squeak',
    };
    const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
    expect(wrapper.vm.$data.localState.value).toBe('Squeak');
    expect(wrapper.vm.$data.localState.static).toBe(true);
    expect(wrapper.find('input').attributes()['readonly']).toBeTruthy();

    wrapper.setProps({ staticValue: 'Oink' });
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.value).toBe('Oink');
    expect(wrapper.vm.$data.localState.static).toBe(true);
    done();
  });

  it('has object value', async done => {
    const obj = { nudl: 'aug' };
    const propsData = {
      label: 'Testhase',
      obj: obj,
      field: 'nudl',
    };
    const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
    expect(wrapper.vm.$data.localState.value).toBe('aug');
    expect(wrapper.vm.$data.localState.static).toBe(false);

    const newObj = { nudl: 'ohr' };
    wrapper.setProps({ obj: newObj });
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.value).toBe('ohr');

    wrapper.find('input').setValue('nase');
    await Vue.nextTick();
    expect(wrapper.vm.$data.localState.value).toBe('nase');
    expect(newObj.nudl).toBe('ohr');

    done();
  });

  allTypes.forEach(type => {
    it(type+' has readonly', async done => {
      const propsData = {
        label: 'Testhase',
        obj: { nudl: 'aug' },
        field: 'nudl',
        readonly: true,
      };
      const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
      expect(wrapper.find('input').attributes()['readonly']).toBeTruthy();

      wrapper.setProps({ readonly: false });
      await Vue.nextTick();
      expect(wrapper.find('input').attributes()['readonly']).toBeFalsy();

      done();
    });
  });

    it('saveValue triggers action and event', async done => {
      actions['testHase'].mockResolvedValue({ 'nudl': 'ohrbohr' });
      const obj = { nudl: 'aug' };
      const propsData = {
        label: 'Testhase',
        obj: obj,
        field: 'nudl',
        action: 'testHase',
      };
      const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
      wrapper.find('input').setValue('ohr');
      (wrapper.vm as any).saveValue();
      expect(wrapper.vm.$data.localState.status).toBe('saving');
      expect(actions['testHase']).toHaveBeenCalledWith(expect.anything(), { 'nudl': 'ohr' });
      await Vue.nextTick();
      await Vue.nextTick();
      expect(wrapper.emitted().updated).toHaveLength(1);
      expect(wrapper.emitted().updated![0]).toStrictEqual([{ nudl: 'ohrbohr' }]);
      expect(wrapper.vm.$data.localState.status).toBe('success');

      expect(obj.nudl).toBe('aug'); // do not change original object
      done();
    });
    it('saveValue failed sets status', async done => {
      actions['testHase'].mockRejectedValue({ fail: 'fail' });

      const obj = { nudl: 'aug' };
      const propsData = {
        label: 'Testhase',
        obj: obj,
        field: 'nudl',
        action: 'testHase',
      };
      const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
      (wrapper.vm as any).saveValue();
      await Vue.nextTick();
      await Vue.nextTick();
      expect(mutations['snackbar/showError']).toHaveBeenCalledWith(expect.anything(), { fail: 'fail' });
      expect(wrapper.vm.$data.localState.status).toBe('failed');
      expect(wrapper.emitted().updated).toBeUndefined();
      done();
    });

    it('saveValue without action triggers only event', async done => {
      const obj = { nudl: 'aug' };
      const propsData = {
        label: 'Testhase',
        obj: obj,
        field: 'nudl',
      };
      const wrapper = mount(TextInput, { localVue, vuetify, store, propsData });
      wrapper.find('input').setValue('ohr');
      (wrapper.vm as any).saveValue();
      expect(wrapper.vm.$data.localState.status).toBe('');

      expect(wrapper.emitted().updated).toHaveLength(1);
      expect(wrapper.emitted().updated![0]).toStrictEqual([{ nudl: 'ohr' }]);
      done();
    });

});