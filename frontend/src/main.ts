import Vue from 'vue'
import VueClipboard from 'vue-clipboard2'
import VueMoment from 'vue-moment';
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify';
import store from './store'

import TopBarComponent from './components/TopBar.vue';
import TextInputComponent from './components/TextInput.vue';
import ContainerStarsComponent from './components/ContainerStars.vue';

import { abbreviate, pluralize, prettyBytes } from '@/util/pretty';

Vue.config.productionTip = false

Vue.component('top-bar', TopBarComponent);
Vue.component('hsk-text-input', TextInputComponent);
Vue.component('container-stars', ContainerStarsComponent);
Vue.use(VueClipboard);
Vue.use(VueMoment);
Vue.filter('abbreviate', abbreviate);
Vue.filter('pluralize', pluralize);
Vue.filter('prettyBytes', prettyBytes);

new Vue({
  router,
  vuetify,
  store,
  render: h => h(App)
}).$mount('#app')

