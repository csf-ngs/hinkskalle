import { createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import Vue from 'vue';

Vue.use(Vuetify);

export const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(VueRouter);