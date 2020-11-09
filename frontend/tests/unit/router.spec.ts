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
    expect(nextFn).toHaveBeenCalledWith({ path: '/login', query: { redirect: to.fullPath }});
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

  it('uses guard', () => {
    router.push('/').then(next => {
      // XXX
    });
  });
});