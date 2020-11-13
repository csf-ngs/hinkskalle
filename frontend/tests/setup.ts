import { createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import VueMoment from 'vue-moment';
import Vue from 'vue';

import TopBarComponent from '@/components/TopBar.vue';

Vue.use(Vuetify);

export const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(VueRouter);
localVue.use(VueMoment);
localVue.component('top-bar', TopBarComponent);
localVue.filter('abbreviate', (v: string) => v);