import router, { isAuthenticated, isAdmin } from '@/router';
import store from '@/store';
import { plainToConfigParams, User } from '@/store/models';
import { Route } from 'vue-router';

import { each as _each } from 'lodash';

const config = plainToConfigParams({
  enable_register: false,
});

describe('AuthGuard', () => {
  it('redirects when not logged in', () => {
    store.state.currentUser = null;
    const nextFn = jest.fn();
    const to = { fullPath: '/oink' } as Route;
    const from = {} as Route;
    isAuthenticated(to, from, nextFn);
    expect(nextFn).toHaveBeenCalledTimes(1);
    expect(nextFn).toHaveBeenCalledWith({ name: 'Login', query: { redirect: to.fullPath }});
  });

  it('continues when logged in', () => {
    store.state.currentUser = { username: 'test.hase' } as User;
    const nextFn = jest.fn();
    const to = {} as Route;
    const from = {} as Route;
    isAuthenticated(to, from, nextFn);
    expect(nextFn).toHaveBeenCalledTimes(1);
    expect(nextFn).toHaveBeenCalledWith();
  });

  it('checks isAdmin', () => {
    const user = new User();
    user.isAdmin = true;
    store.state.currentUser = user;
    const nextFn = jest.fn();
    const to = {} as Route;
    const from = {} as Route;
    isAdmin(to, from, nextFn);
    expect(nextFn).toHaveBeenCalledTimes(1);
    expect(nextFn).toHaveBeenCalledWith();
  });

  it('throws if not admin', () => {
    const user = new User();
    user.isAdmin = false;
    store.state.currentUser = user;
    const nextFn = jest.fn();
    const to = {} as Route;
    const from = {} as Route;
    isAdmin(to, from, nextFn);
    expect(nextFn).toHaveBeenCalledWith(Error('Admin privileges required'));
  });

  it('throws if user undef', () => {
    store.state.currentUser = null;
    const nextFn = jest.fn();
    const to = {} as Route;
    const from = {} as Route;
    isAdmin(to, from, nextFn);
    expect(nextFn).toHaveBeenCalledWith(Error('Admin privileges required'));
  });

  store.state.config = config;
  _each([
        '/tokens', 
        '/account', 
        '/collections', 
        '/entities', 
        '/entities/wumm/collections', 
        '/entities/wumm/collections/bumm/containers', 
        '/entities/wumm/collections/bumm/containers/trumm', 
        '/users',
        '/ldap',
      ], route => {
    it(`requires auth for ${route}`, async () => {
      store.state.currentUser = null;
      try {
        await router.push(route);
      }
      catch(err) {
        // ignore
      }
      expect(router.currentRoute.fullPath).toBe(`/login?redirect=${encodeURIComponent(route)}`);

      store.state.currentUser = { username: 'test.hase' } as User;
      await router.push(route);
      expect(router.currentRoute.fullPath).toBe(route);

    });
  });
  _each([
        '/users',
        '/ldap',
    ], route => {
      it.skip(`requires admin for ${route}`, async () => {
        store.state.config = config;
        await router.push('/').catch(err => {});
        store.state.currentUser = { isAdmin: false } as User;
        await router.push(route);
        expect(router.currentRoute.fullPath).toBe('/');

        store.state.currentUser = { isAdmin: true } as User;
        await router.push(route);
        expect(router.currentRoute.fullPath).toBe(route);
      });
    });
});