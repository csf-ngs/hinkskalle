import Vue from 'vue';
import VueRouter, { RouteConfig, NavigationGuard } from 'vue-router';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Tokens from '../views/Tokens.vue';
import Account from '../views/Account.vue';
import Collections from '../views/Collections.vue';
import Entities from '../views/Entities.vue';
import Groups from '../views/Groups.vue';
import Containers from '../views/Containers.vue';
import ContainerDetails from '../views/ContainerDetails.vue';
import Users from '../views/Users.vue';
import Ldap from '../views/Ldap.vue';
import About from '../views/About.vue';
import Tasks from '../views/Tasks.vue';
import store from '../store';

Vue.use(VueRouter);

export const isAuthenticated: NavigationGuard = (to, from, next) => {
  if (!store.getters.isLoggedIn) {
    return next(from.name === 'Login' ? false : {
      name: 'Login',
      query: { redirect: to.fullPath },
    });
  }
  else {
    return next();
  }
};

export const isAdmin: NavigationGuard = (to, from, next) => {
  if (!store.getters.currentUser || !store.getters.currentUser.isAdmin) {
    return next(new Error("Admin privileges required"));
  }
  else {
    return next();
  }
}

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
    path: '/about',
    name: 'About',
    component: About,
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
    path: '/tokens/:user',
    name: 'AdminTokens',
    component: Tokens,
    meta: { requiresAdmin: true, requiresAuth: true },
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
    path: '/groups',
    name: 'Groups',
    component: Groups,
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
  {
    path: '/entities/:entity/collections/:collection/containers/:container',
    name: 'ContainerDetails',
    component: ContainerDetails,
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'Users',
    component: Users,
    meta: { requiresAdmin: true, requiresAuth: true, },
  },
  {
    path: '/ldap',
    name: 'Ldap',
    component: Ldap,
    meta: { requiresAdmin: true, requiresAuth: true, },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: { requiresAdmin: true, requiresAuth: true, },
  },
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
});

const DEFAULT_TITLE = 'Hinkskalle';

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    return isAuthenticated(to, from, next);
  }
  if (to.matched.some(record => record.meta.requiresAdmin)) {
    return isAdmin(to, from, next);
  }
  next();
});
router.afterEach((to) => {
  Vue.nextTick(() => {
    document.title = (to.meta && to.meta.title) || to.fullPath || DEFAULT_TITLE;
  });
});

export default router
