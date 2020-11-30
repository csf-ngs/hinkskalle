import store from '@/store';
import {User, plainToUser, serializeUser} from '@/store/models';

import axios from 'axios';

import { clone as _clone, find as _find } from 'lodash';

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
  it('has list getter', () => {
    store.state.users!.list = [ testUserObj ];
    expect(store.getters['users/list']).toStrictEqual([ testUserObj ]);
  })
});

describe('user mutations', () => {
  it('has status mutations', () => {
    store.state.users!.status = '';
    store.commit('users/loading');
    expect(store.state.users!.status).toBe('loading');
    store.commit('users/succeeded');
    expect(store.state.users!.status).toBe('success');
    store.commit('users/failed');
    expect(store.state.users!.status).toBe('failed');
  });

  it('has set starred', () => {
    const test = makeTestContainersObj();
    store.state.users!.starred = [];
    store.commit('users/setStarred', test);
    expect(store.state.users!.starred).toStrictEqual(test);
  });

  it('has setList mutation', () => {
    store.state.users!.list = [];
    store.commit('users/setList', [ testUserObj ]);
    expect(store.state.users!.list).toStrictEqual([ testUserObj ]);
  });

  it('has update user mutation', () => {
    const list = [ makeTestUserObj(), makeTestUserObj() ];
    list[0].id="1";
    list[1].id="2";
    store.state.users!.list = list;

    const update = _clone(list[0]);
    update.email = 'oink@oi.nk';
    store.commit('users/update', update);
    
    const updated = _find(store.state.users!.list, u => u.id === update.id);
    expect(updated).toStrictEqual(update);
    expect(store.state.users!.list).toHaveLength(2);

    const create = new User();
    create.id="999";
    create.email = 'tin@ti.fax';

    store.commit('users/update', create);
    expect(store.state.users!.list).toHaveLength(3);
    const added = _find(store.state.users!.list, u => u.id === create.id);
    expect(added).toStrictEqual(create);
  });

  it('has remove mutation', () => {
    const list = [ makeTestUserObj(), makeTestUserObj() ];
    list[0].id="1";
    list[1].id="2";
    store.state.users!.list = list;

    store.commit('users/remove', list[0].id);
    expect(store.state.users!.list).toHaveLength(1);
    const removed = _find(store.state.users!.list, u => u.id === list[0].id);
    expect(removed).toBeUndefined();
  });
});

describe('user store actions', () => {
  it('has update user', done => {
    const updateUser = makeTestUser();
    updateUser.id = "111";
    store.state.users!.list = [ plainToUser(updateUser) ];

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
      const updated = _find(store.state.users!.list, u => u.id === updateUser.id);
      expect(updated).toStrictEqual(updateUserObj);
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
    store.state.users!.list = [ testUserObj ];

    const promise = store.dispatch('users/delete', testUserObj);
    expect(mockAxios.delete).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}`);
    expect(store.state.users!.status).toBe('loading');
    promise.then(ret => {
      expect(store.state.users!.status).toBe('success');
      expect(store.state.users!.list).toHaveLength(0);
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
    store.state.users!.starsLoaded = false;
    const test = makeTestContainers();
    const testObj = makeTestContainersObj(test);
    mockAxios.get.mockResolvedValue({ data: { data: test }});
    const promise = store.dispatch('users/getStarred');
    expect(store.state.users!.status).toBe('loading');
    promise.then(ret => {
      expect(store.state.users!.starsLoaded).toBeTruthy();
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/users/${testUserObj.username}/stars`);
      expect(store.state.users!.status).toBe('success');
      expect(store.state.users!.starred).toStrictEqual(testObj);
      expect(ret).toStrictEqual(testObj);
      done();
    });
  });
  it('does not reload starred containers', done => {
    store.state.users!.starsLoaded = true;
    const testObj = makeTestContainersObj();
    store.state.users!.starred = testObj;
    mockAxios.get.mockReset();
    mockAxios.get.mockResolvedValue({});
    store.dispatch('users/getStarred')
      .then(ret => {
        expect(ret).toStrictEqual(testObj);
        expect(mockAxios.get).toHaveBeenCalledTimes(0);
        done();
      });
  });
  it('has list starred fail handling', done => {
    store.state.users!.starsLoaded=false;
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/getStarred')
      .catch(err => {
        expect(store.state.users!.status).toBe('failed');
        expect(store.state.users!.starsLoaded).toBeFalsy();
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

  it('has load user list', done => {
    const testUser = makeTestUser();
    const testObj = makeTestUserObj(testUser);
    mockAxios.get.mockResolvedValue({
      data: { data: [ testUser ]},
    });
    const promise = store.dispatch('users/list');
    expect(store.state.users!.status).toBe('loading');
    promise.then(list => {
      expect(mockAxios.get).toHaveBeenLastCalledWith(`/v1/users`);
      expect(store.state.users!.status).toBe('success');
      expect(store.state.users!.list).toStrictEqual([ testObj ]);
      expect(list).toStrictEqual([ testObj ]);
      done();
    });
  });
  it('has load user list fail handling', done => {
    mockAxios.get.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/list')
      .catch(err => {
        expect(store.state.users!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });

  it('has create user', done => {
    const user = {
      username: 'test.hase',
    };
    const createUserObj = plainToUser(user);

    mockAxios.post.mockResolvedValue({
      data: { data: { id: '666', username: user.username }}
    });

    const promise = store.dispatch('users/create', createUserObj);
    expect(store.state.users!.status).toBe('loading');
    promise.then(user => {
      expect(mockAxios.post).toHaveBeenLastCalledWith(`/v1/users`, serializeUser(createUserObj));
      expect(store.state.users!.status).toBe('success');
      const created = _find(store.state.users!.list, u => u.id === '666');
      if (!created) {
        throw Error('created id 666 not found');
      }
      createUserObj.id = created.id;
      expect(created).toStrictEqual(createUserObj);
      expect(user).toStrictEqual(createUserObj);
      done();
    });
  });

  it('has create user fail handling', done => {
    mockAxios.post.mockRejectedValue({ fail: 'fail' });
    store.dispatch('users/create', testUserObj)
      .catch(err => {
        expect(store.state.users!.status).toBe('failed');
        expect(err).toStrictEqual({ fail: 'fail' });
        done();
      });
  });
    
});