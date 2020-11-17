import Vue from 'vue';
import VueRouter, { RouteConfig, NavigationGuard } from 'vue-router';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Tokens from '../views/Tokens.vue';
import Account from '../views/Account.vue';
import Collections from '../views/Collections.vue';
import Entities from '../views/Entities.vue';
import Containers from '../views/Containers.vue';
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
    path: '/account',
    name: 'Account',
    component: Account,
    meta: { requiresAuth: true },
  },
  {
    path: '/tokens',
    name: 'Tokens',
    component: Tokens,
    meta: { requiresAuth: true },
  },
  {
    path: '/collections',
    name: 'Collections',
    component: Collections,
    meta: { requiresAuth: true },
  },
  {
    path: '/entities',
    name: 'Entities',
    component: Entities,
    meta: { requiresAuth: true },
  },
  {
    path: '/entities/:entity/collections',
    name: 'EntityCollections',
    component: Collections,
    meta: { requiresAuth: true },
  },
  {
    path: '/entities/:entity/collections/:collection/containers',
    name: 'Containers',
    component: Containers,
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
