import store from '@/store';

import { AxiosError } from 'axios';

describe('snackbar store getters', () => {
  it('has showSnackbar getter', () => {
    store.state.snackbar!.show = false;
    expect(store.getters['snackbar/show']).toBe(false);
    store.state.snackbar!.show = true;
    expect(store.getters['snackbar/show']).toBe(true);
  });
  it('has snackbarMsg getter', () => {
    store.state.snackbar!.msg = 'oink';
    expect(store.getters['snackbar/msg']).toBe('oink');
  });
});

describe('snackbar store mutations', () => {
  it('has open', () => {
    store.commit('snackbar/open', 'Oink!');
    expect(store.state.snackbar!.msg).toBe('Oink!');
    expect(store.state.snackbar!.show).toBe(true);
  });

  it('has close', () => {
    store.commit('snackbar/close');
    expect(store.state.snackbar!.msg).toBe('');
    expect(store.state.snackbar!.show).toBe(false);
  });

  it('has showSuccess', () => {
    store.commit('snackbar/showSuccess', 'Yeehaw');
    expect(store.state.snackbar!.type).toBe('success');
    expect(store.state.snackbar!.msg).toBe('Yeehaw');
    expect(store.state.snackbar!.show).toBe(true);
  });

  it('has showError string', () => {
    store.commit('snackbar/showError', 'Onoz!');
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Onoz!');
  });

  const createError = (): AxiosError => ({
      message: '',
      config: {},
      isAxiosError: true,
      name: '',
      toJSON: () => ({}),
  });
  it('has showError Axios error list response', () => {
    const err = createError();
    err.response = {
      status: 500,
      statusText: 'Infernal Swerver Mirror',
      config: {},
      headers: {},
      data: {
        errors: [ { message: 'EFAIL' } ]
      }
    };
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Code 500: EFAIL');
  });

  it('has showError Axios error message response', () => {
    const err = createError();
    err.response = {
      status: 500,
      statusText: 'Infernal Swerver Mirror',
      config: {},
      headers: {},
      data: {
        message: 'EFAIL',
      }
    };
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Code 500: EFAIL');
  });

  it('has showError Axios error unauthorized response', () => {
    const err = createError();
    err.response = {
      status: 401,
      statusText: 'Go away',
      config: {},
      headers: {},
      data: {},
    };
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Code 401: Unauthorized! Go away');
  });

  it('has showError Axios error other response', () => {
    const err = createError();
    err.response = {
      status: 500,
      statusText: 'Something is broken',
      config: {},
      headers: {},
      data: {},
    };
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Code 500: Something is broken');
  });

  it('has showError Axios request error', () => {
    const err = createError();
    err.request = {
      something: 'does not matter',
    };
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Upstream may have died, or your network sucks.');
  });

  it('has showError Axios message fallback', () => {
    const err = createError();
    err.message = "Wuff Zack";
    store.commit('snackbar/showError', err);
    expect(store.state.snackbar!.type).toBe('error');
    expect(store.state.snackbar!.show).toBe(true);
    expect(store.state.snackbar!.msg).toBe('Wuff Zack');
  });
});