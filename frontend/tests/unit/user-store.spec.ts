import store from '@/store';
import {plainToUser, serializeUser} from '@/store/models';

import axios from 'axios';

import { clone as _clone } from 'lodash';

import { testUser, testUserObj } from './store.spec';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

describe('user store getters', () => {
  it('has status getter', () => {
    store.state.users!.status = 'loading';
    expect(store.getters['users/status']).toBe('loading');
  });
});

describe('user store actions', () => {
  it('has update user', done => {
    const updateUser = _clone(testUser);
    updateUser.firstname = 'Oink!';

    const updateUserObj = plainToUser(updateUser);

    mockAxios.put.mockResolvedValue({
      data: { data: updateUser } 
    });
    const promise = store.dispatch('users/update', updateUserObj);
    expect(mockAxios.put).toHaveBeenLastCalledWith(`/v1/users/${updateUserObj.username}`, serializeUser(updateUserObj));
    expect(store.state.users!.status).toBe('loading');
    promise.then(user => {
      expect(store.state.users!.status).toBe('success');
      expect(user).toStrictEqual(updateUserObj);
      done();
    });
  });
  it('has update user fail handling', done => {
    mockAxios.put.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/update', testUserObj).catch(err => {
      expect(store.state.users!.status).toBe('failed');
      done();
    });
  });

  it('has delete user', done => {
    mockAxios.delete.mockResolvedValue({
      status: 'ok',
    });

    const promise = store.dispatch('users/delete', testUserObj);
    expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}`);
    expect(store.state.users!.status).toBe('loading');
    promise.then(ret => {
      expect(store.state.users!.status).toBe('success');
      done();
    });
  });
  it('has delete user fail handling', done => {
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/delete', testUser).catch(err => {
      expect(store.state.users!.status).toBe('failed');
      done();
    });
  });
});