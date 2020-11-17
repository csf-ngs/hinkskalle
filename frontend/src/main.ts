import Vue from 'vue'
import VueClipboard from 'vue-clipboard2'
import VueMoment from 'vue-moment';
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify';
import store from './store'

import TopBarComponent from './components/TopBar.vue';

Vue.config.productionTip = false

new Vue({
  router,
  vuetify,
  store,
  render: h => h(App)
}).$mount('#app')


Vue.use(VueClipboard);
Vue.use(VueMoment);
Vue.component('top-bar', TopBarComponent);
Vue.filter('abbreviate', function(value: string, maxlen: number): string {
  if (isNaN(maxlen)) maxlen=20;
  return value.substr(0, maxlen)+(value.length>maxlen ? '...' : '');
});
Vue.filter('pluralize', function(value: number, word: string): string {
  return value === 1 ? word : `${word}s`;
});