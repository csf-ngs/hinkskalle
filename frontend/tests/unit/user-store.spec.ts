import store from '@/store';
import {User, plainToUser, serializeUser} from '@/store/models';

import axios from 'axios';

import { clone as _clone } from 'lodash';

import { makeTestUser, makeTestUserObj } from '../_data';
import { makeTestContainers, makeTestContainersObj } from '../_data';

jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

store.state.backend = mockAxios;

let testUserObj: User;
beforeAll(() => {
  testUserObj = makeTestUserObj();
});

describe('user store getters', () => {
  it('has status getter', () => {
    store.state.users!.status = 'loading';
    expect(store.getters['users/status']).toBe('loading');
  });
  it('has starred getter', () => {
    const test = makeTestContainersObj();
    store.state.users!.starred = test;
    expect(store.getters['users/starred']).toStrictEqual(test);
  });
});

describe('user mutations', () => {
  it('has set starred', () => {
    const test = makeTestContainersObj();
    store.state.users!.starred = [];
    store.commit('users/setStarred', test);
    expect(store.state.users!.starred).toStrictEqual(test);
  });
});

describe('user store actions', () => {
  it('has update user', done => {
    const updateUser = makeTestUser();
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
    store.dispatch('users/delete', makeTestUser()).catch(err => {
      expect(store.state.users!.status).toBe('failed');
      done();
    });
  });

  it('can list starred containers', done => {
    store.state.currentUser = testUserObj;
    const test = makeTestContainers();
    const testObj = makeTestContainersObj(test);
    mockAxios.get.mockResolvedValue({ data: { data: test }});
    const promise = store.dispatch('users/getStarred');
    expect(store.state.users!.status).toBe('loading');
    promise.then(ret => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/stars`);
      expect(store.state.users!.status).toBe('success');
      expect(store.state.users!.starred).toStrictEqual(testObj);
      expect(ret).toStrictEqual(testObj);
      done();
    });
  });
  it('has list starred fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/getStarred')
      .catch(err => {
        expect(store.state.users!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('can star a container', done => {
    store.state.currentUser = testUserObj;
    const test = makeTestContainers();
    const testObj = makeTestContainersObj(test);

    mockAxios.post.mockResolvedValue({
      data: { data: test }
    });
    const promise = store.dispatch('users/addStar', testObj[0]);
    expect(store.state.users!.status).toBe('loading');
    promise.then(ret => {
      expect(store.state.users!.status).toBe('success');
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/stars/${testObj[0].id}`);
      expect(store.state.users!.starred).toStrictEqual(testObj);
      expect(ret).toStrictEqual(testObj);
      done();
    });
  });

  it('has star container fail handling', done => {
    store.state.currentUser = testUserObj;
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/addStar', makeTestContainersObj()[0])
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.users!.status).toBe('failed');
        done();
      });
  });

  it('can remove star', done => {
    store.state.currentUser = testUserObj;
    const test = makeTestContainers();
    const testObj = makeTestContainersObj(test);

    mockAxios.delete.mockResolvedValue({
      data: { data: test }
    });
    const promise = store.dispatch('users/removeStar', testObj[0]);
    promise.then(ret => {
      expect(store.state.users!.status).toBe('success');
      expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/stars/${testObj[0].id}`);
      expect(store.state.users!.starred).toStrictEqual(testObj);
      expect(ret).toStrictEqual(testObj);
      done();
    });
  });
  it('has remove star fail handling', done => {
    store.state.currentUser = testUserObj;
    mockAxios.delete.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/removeStar', makeTestContainersObj()[0])
      .catch(err => {
        expect(err).toStrictEqual({ fail: 'fail' });
        expect(store.state.users!.status).toBe('failed');
        done();
      });
  });
    
});