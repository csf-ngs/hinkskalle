import Vue from 'vue';
import VueRouter, { RouteConfig, NavigationGuard } from 'vue-router';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Tokens from '../views/Tokens.vue';
import store from '../store';

Vue.use(VueRouter);

export const isAuthenticated: NavigationGuard = (to, _, next) => {
  if (!store.getters.isLoggedIn) {
    return next({
      name: 'Login',
      query: { redirect: to.fullPath },
    });
  }
  else {
    return next();
  }
};

const routes: Array<RouteConfig> = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  { 
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/tokens',
    name: 'Tokens',
    component: Tokens,
    meta: { requiresAuth: true },
  },
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
});

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    return isAuthenticated(to, from, next);
  }
  next();
});

export default router
