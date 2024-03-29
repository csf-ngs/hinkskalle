import { createLocalVue } from '@vue/test-utils';
import Vuex from 'vuex';
import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import VueMoment from 'vue-moment';
import Vue from 'vue';

import TopBarComponent from '@/components/TopBar.vue';
import TextInput from '@/components/TextInput.vue';
import ContainerStars from '@/components/ContainerStars.vue';
import ErrorMessageComponent from '@/components/ErrorMessage.vue';

Vue.use(Vuetify);

const prettyBytes = (v: undefined | number): string => v ? v.toString() : '';

export const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(VueRouter);
localVue.use(VueMoment);
localVue.component('top-bar', TopBarComponent);
localVue.component('hsk-text-input', TextInput);
localVue.component('container-stars', ContainerStars);
localVue.component('error-message', ErrorMessageComponent);
localVue.filter('abbreviate', (v: string) => v);
localVue.filter('pluralize', (v: number, w: string) => w);
localVue.filter('prettyBytes', prettyBytes);
localVue.filter('prettyDateTime', (v: Date): string => v ? v.toISOString() : '-' );

export const localVueNoRouter = createLocalVue();
localVueNoRouter.use(Vuex);
localVueNoRouter.use(VueMoment);
localVueNoRouter.component('top-bar', TopBarComponent);
localVueNoRouter.component('hsk-text-input', TextInput);
localVueNoRouter.component('container-stars', ContainerStars);
localVueNoRouter.filter('abbreviate', (v: string) => v);
localVueNoRouter.filter('pluralize', (v: number, w: string) => w);
localVueNoRouter.filter('prettyBytes', prettyBytes);
