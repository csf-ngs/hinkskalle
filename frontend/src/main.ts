import Vue from 'vue'
import VueClipboard from 'vue-clipboard2'
import VueMoment from 'vue-moment';
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify';
import store from './store'

import TopBarComponent from './components/TopBar.vue';
import TextInputComponent from './components/TextInput.vue';

Vue.config.productionTip = false

Vue.component('top-bar', TopBarComponent);
Vue.component('hsk-text-input', TextInputComponent);
Vue.use(VueClipboard);
Vue.use(VueMoment);
Vue.filter('abbreviate', function(value: string, maxlen: number): string {
  if (isNaN(maxlen)) maxlen=20;
  return value.substr(0, maxlen)+(value.length>maxlen ? '...' : '');
});
Vue.filter('pluralize', function(value: number, word: string): string {
  return value === 1 ? word : `${word}s`;
});
Vue.filter('prettyBytes', function (num: number): string {
  // jacked from: https://github.com/sindresorhus/pretty-bytes
  if (typeof num !== 'number' || isNaN(num)) {
    throw new TypeError('Expected a number');
  }

  const neg = num < 0;
  const units = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  if (neg) {
    num = -num;
  }

  if (num < 1) {
    return (neg ? '-' : '') + num + ' B';
  }

  const exponent = Math.min(Math.floor(Math.log(num) / Math.log(1000)), units.length - 1);
  const outNum = (num / Math.pow(1000, exponent)).toFixed(2);
  const unit = units[exponent];

  return `${neg ? '-' : ''}${outNum} ${unit}`;
});

new Vue({
  router,
  vuetify,
  store,
  render: h => h(App)
}).$mount('#app')

