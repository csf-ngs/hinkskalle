import axios from 'axios';

import { Container, plainToContainer, Upload, plainToUpload, User, plainToUser, Collection, plainToCollection, Entity, plainToEntity, SearchResult, plainToSearchResult, plainToGroup, Group } from '@/store/models';

import { map as _map } from 'lodash';

export function makeTestUser() {
  return {
    id: "1",
    username: 'test.hase',
    email: 'test@ha.se',
    firstname: 'Test',
    lastname: 'Hase',
    isAdmin: false,
  }
}

export function makeTestUserObj(from: any=null): User {
  return plainToUser(from || makeTestUser());
}

export function makeTestGroup() {
  return {
    id: "1",
    name: "Testhasentall",
    email: "stall@testha.se",
    description: "oink",
  }
}

export function makeTestGroupObj(from: any=null): Group {
  return plainToGroup(from || makeTestGroup())
}

export function makeTestContainers() {
  return [
    { id: "1", name: "testhippo", collectionName: "oinktion", entityName: "oinktity", description: 'Nilpferd', createdAt: new Date(), stars: 0, type: 'singularity' },
    { id: "2", name: "testzebra", collectionName: "muhtion", entityName: "muhtity", description: 'Streifig', createdAt: new Date(), stars: 0, type: 'mixed' },
  ]
}

export function makeTestContainersObj(from: any=null): Container[] {
  return _map(from || makeTestContainers(), plainToContainer);
}

export function makeTestLatest() {
  return [
    { 
      tags: ['eins', 'zwei'], 
      container: {
        name: 'testhase', createdAt: new Date(), collectionName: 'oinkton', entityName: 'oinktity',
      },
    },
    {
      tags: ['drei', 'vier'],
      container: {
        name: 'testnilpferd', createdAt: new Date(), collectionName: 'muhton', entityName: 'muhtity',
      },
    }
  ];
}
export function makeTestLatestObj(from: any=null): Upload[] {
  return _map(from || makeTestLatest(), plainToUpload);
}

export function makeTestCollections() {
  return [
    {
      id: '1', name: 'esel', description: 'eyore', createdAt: new Date(), entityName: 'oinktity', canEdit: true,
    },
    {
      id: '2', name: 'schaf', description: 'shawn', createdAt: new Date(), entityName: 'wooftity', canEdit: true,
    }
  ];
}

export function makeTestCollectionsObj(from: any=null): Collection[] {
  return _map(from || makeTestCollections(), plainToCollection);
}

export function makeTestEntities() {
  return [
    {
      id: '1', name: 'esel', description: 'eyore', createdAt: new Date(), quota: 0, canEdit: true,
    },
    {
      id: '2', name: 'schaf', description: 'shawn', createdAt: new Date(), quota: 0, canEdit: true,
    }
  ];
}

export function makeTestEntitiesObj(from: any=null): Entity[] {
  return _map(from || makeTestEntities(), plainToEntity);
}

export function makeTestSearchResult() {
  return {
    entity: makeTestEntities(),
    collection: makeTestCollections(),
    container: makeTestContainers(),
    image: []
  }
}
export function makeTestSearchResultObj(from: any=null): SearchResult {
  return plainToSearchResult(from || makeTestSearchResult());
}