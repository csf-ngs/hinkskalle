import router, { isAuthenticated } from '@/router';
import store from '@/store';
import { User } from '@/store/models';
import { Route } from 'vue-router';

import { each as _each } from 'lodash';

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

  _each(['/tokens', '/account', '/collections'], route => {
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
});