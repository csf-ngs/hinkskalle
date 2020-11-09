import router, { isAuthenticated } from '@/router';
import store from '@/store';
import { User } from '@/store/models';
import { Route } from 'vue-router';

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

  it('requires auth for tokens', async () => {
    store.state.currentUser = null;
    try {
      await router.push('/tokens');
    }
    catch(err) {
      // ignore
    }
    expect(router.currentRoute.fullPath).toBe('/login?redirect=%2Ftokens');

    store.state.currentUser = { username: 'test.hase' } as User;
    await router.push('/tokens');
    expect(router.currentRoute.fullPath).toBe('/tokens');

  });
});