import { createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import VueMoment from 'vue-moment';
import Vue from 'vue';

import TopBarComponent from '@/components/TopBar.vue';

Vue.use(Vuetify);

const prettyBytes = (v: undefined | number): string => v ? v.toString() : '';

export const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(VueRouter);
localVue.use(VueMoment);
localVue.component('top-bar', TopBarComponent);
localVue.filter('abbreviate', (v: string) => v);
localVue.filter('pluralize', (v: number, w: string) => w);
localVue.filter('prettyBytes', prettyBytes);

export const localVueNoRouter = createLocalVue();
localVueNoRouter.use(Vuex);
localVueNoRouter.use(VueMoment);
localVueNoRouter.component('top-bar', TopBarComponent);
localVueNoRouter.filter('abbreviate', (v: string) => v);
localVueNoRouter.filter('pluralize', (v: number, w: string) => w);
localVueNoRouter.filter('prettyBytes', prettyBytes);
