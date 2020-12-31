// autogenerated with `flask create-typescript-models`, do not edit directly.
import { isNil as _isNil, map as _map } from 'lodash';



class Collection {
  public containers!: string
  public createdAt!: Date | null
  public createdBy!: string
  public customData!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public entity!: string
  public entityName!: string
  public id!: string
  public name!: string
  public private!: boolean
  public size!: number
  public updatedAt!: Date | null
  

  public get collectionName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}/${this.name}`
  }
  
  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }
}

export function plainToCollection(json: any): Collection {
  const obj = new Collection();
  obj.containers = json['containers'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.customData = json['customData'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.entity = json['entity'];
    obj.entityName = json['entityName'];
    obj.id = json['id'];
    obj.name = json['name'];
    obj.private = json['private'];
    obj.size = json['size'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      
  return obj;
}
export function serializeCollection(obj: Collection, unroll=false): any {
  const json: any = {};
  json['createdBy'] = obj.createdBy
      json['customData'] = obj.customData
      json['description'] = obj.description
      json['entity'] = obj.entity
      json['name'] = obj.name
      json['private'] = obj.private
      
  return json;
}


export { Collection };


class Container {
  public archTags!: object
  public collection!: string
  public collectionName!: string
  public createdAt!: Date | null
  public createdBy!: string
  public customData!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public downloadCount!: number
  public entity!: string
  public entityName!: string
  public fullDescription!: string
  public id!: string
  public imageTags!: object
  public images!: string
  public name!: string
  public private!: boolean
  public readOnly!: boolean
  public size!: number
  public stars!: number
  public updatedAt!: Date | null
  public vcsUrl!: string
  

  public get containerName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}/${this.collectionName}/${this.name}`
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }
}

export function plainToContainer(json: any): Container {
  const obj = new Container();
  obj.archTags = json['archTags'];
    obj.collection = json['collection'];
    obj.collectionName = json['collectionName'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.customData = json['customData'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.downloadCount = json['downloadCount'];
    obj.entity = json['entity'];
    obj.entityName = json['entityName'];
    obj.fullDescription = json['fullDescription'];
    obj.id = json['id'];
    obj.imageTags = json['imageTags'];
    obj.images = json['images'];
    obj.name = json['name'];
    obj.private = json['private'];
    obj.readOnly = json['readOnly'];
    obj.size = json['size'];
    obj.stars = json['stars'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.vcsUrl = json['vcsUrl'];
    
  return obj;
}
export function serializeContainer(obj: Container, unroll=false): any {
  const json: any = {};
  json['collection'] = obj.collection
      json['createdBy'] = obj.createdBy
      json['customData'] = obj.customData
      json['description'] = obj.description
      json['fullDescription'] = obj.fullDescription
      json['name'] = obj.name
      json['private'] = obj.private
      json['readOnly'] = obj.readOnly
      json['vcsUrl'] = obj.vcsUrl
      
  return json;
}


export { Container };


class Entity {
  public collections!: string
  public createdAt!: Date | null
  public createdBy!: string
  public customData!: string
  public defaultPrivate!: boolean
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public id!: string
  public name!: string
  public quota!: number
  public size!: number
  public updatedAt!: Date | null
  

  public get entityName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}`
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }
  
}

export function plainToEntity(json: any): Entity {
  const obj = new Entity();
  obj.collections = json['collections'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.customData = json['customData'];
    obj.defaultPrivate = json['defaultPrivate'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.id = json['id'];
    obj.name = json['name'];
    obj.quota = json['quota'];
    obj.size = json['size'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      
  return obj;
}
export function serializeEntity(obj: Entity, unroll=false): any {
  const json: any = {};
  json['createdBy'] = obj.createdBy
      json['customData'] = obj.customData
      json['defaultPrivate'] = obj.defaultPrivate
      json['description'] = obj.description
      json['name'] = obj.name
      
  return json;
}


export { Entity };


class Image {
  public blob!: string
  public collection!: string
  public collectionName!: string
  public container!: string
  public containerDownloads!: number
  public containerName!: string
  public containerStars!: number
  public createdAt!: Date | null
  public createdBy!: string
  public customData!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public downloadCount!: number
  public entity!: string
  public entityName!: string
  public hash!: string
  public id!: string
  public size!: number
  public tags!: string[]
  public updatedAt!: Date | null
  public uploaded!: boolean
  

  public get fullPath(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}:${this.hash}`
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }
}

export function plainToImage(json: any): Image {
  const obj = new Image();
  obj.blob = json['blob'];
    obj.collection = json['collection'];
    obj.collectionName = json['collectionName'];
    obj.container = json['container'];
    obj.containerDownloads = json['containerDownloads'];
    obj.containerName = json['containerName'];
    obj.containerStars = json['containerStars'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.customData = json['customData'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.downloadCount = json['downloadCount'];
    obj.entity = json['entity'];
    obj.entityName = json['entityName'];
    obj.hash = json['hash'];
    obj.id = json['id'];
    obj.size = json['size'];
    obj.tags = json['tags'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.uploaded = json['uploaded'];
    
  return obj;
}
export function serializeImage(obj: Image, unroll=false): any {
  const json: any = {};
  json['blob'] = obj.blob
      json['container'] = obj.container
      json['customData'] = obj.customData
      json['description'] = obj.description
      json['hash'] = obj.hash
      json['uploaded'] = obj.uploaded
      
  return json;
}

export interface InspectAttributes {
  deffile: string;
}

export { Image };


class Group {
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public email!: string
  public id!: string
  public name!: string
  public updatedAt!: Date | null
  
}

export function plainToGroup(json: any): Group {
  const obj = new Group();
  obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.email = json['email'];
    obj.id = json['id'];
    obj.name = json['name'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      
  return obj;
}
export function serializeGroup(obj: Group, unroll=false): any {
  const json: any = {};
  json['email'] = obj.email
      json['name'] = obj.name
      
  return json;
}

export { Group };


class User {
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public email!: string
  public firstname!: string
  public groups!: Group[]
  public id!: string
  public isActive!: boolean
  public isAdmin!: boolean
  public lastname!: string
  public source!: string
  public updatedAt!: Date | null
  public username!: string
  

  public password?: string
  public oldPassword?: string

  public get fullname(): string {
    return `${this.firstname} ${this.lastname}`;
  }

  public get role(): 'admin' | 'user' {
    return this.isAdmin ? 'admin' : 'user';
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.username===user.username);
  }

  public stars: Container[] = []
}

export function plainToUser(json: any): User {
  const obj = new User();
  obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.email = json['email'];
    obj.firstname = json['firstname'];
    if (!_isNil(json['groups'])) obj.groups = _map(json['groups'], plainToGroup);
      obj.id = json['id'];
    obj.isActive = json['isActive'];
    obj.isAdmin = json['isAdmin'];
    obj.lastname = json['lastname'];
    obj.source = json['source'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.username = json['username'];
    
  return obj;
}
export function serializeUser(obj: User, unroll=false): any {
  const json: any = {};
  json['email'] = obj.email
      json['firstname'] = obj.firstname
      if (unroll) json['groups'] = _isNil(obj.groups) ? [] : _map(obj.groups, f => serializeGroup(f));
        json['isActive'] = obj.isActive
      json['isAdmin'] = obj.isAdmin
      json['lastname'] = obj.lastname
      json['source'] = obj.source
      json['username'] = obj.username
      
  if (obj.password) {
    json['password']=obj.password;
  }
  if (obj.oldPassword) {
    json['oldPassword']=obj.oldPassword;
  }
  return json;
}

export { User };


class Token {
  public comment!: string
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public expiresAt!: Date | null
  public id!: string
  public source!: string
  public token!: string
  public updatedAt!: Date | null
  public user!: User
  
}

export function plainToToken(json: any): Token {
  const obj = new Token();
  obj.comment = json['comment'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.expiresAt = _isNil(json['expiresAt']) ? null : new Date(json['expiresAt']);
      obj.id = json['id'];
    obj.source = json['source'];
    obj.token = json['token'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      if (!_isNil(json['user'])) obj.user = plainToUser(json['user']);
      
  return obj;
}
export function serializeToken(obj: Token, unroll=false): any {
  const json: any = {};
  json['comment'] = obj.comment
      json['expiresAt'] = _isNil(obj.expiresAt) ? null : obj.expiresAt.toJSON();
        if (unroll) json['user'] = _isNil(obj.user) ? null : serializeUser(obj.user);
        
  return json;
}

export { Token };


class Job {
  public dependson!: string
  public description!: string
  public endedAt!: string
  public enqueuedAt!: string
  public excInfo!: string
  public failureTTL!: number
  public funcName!: string
  public id!: string
  public meta!: object
  public origin!: string
  public result!: string
  public resultTTL!: number
  public startedAt!: string
  public status!: string
  public timeout!: string
  public ttl!: number
  
}

export function plainToJob(json: any): Job {
  const obj = new Job();
  obj.dependson = json['dependson'];
    obj.description = json['description'];
    obj.endedAt = json['endedAt'];
    obj.enqueuedAt = json['enqueuedAt'];
    obj.excInfo = json['excInfo'];
    obj.failureTTL = json['failureTTL'];
    obj.funcName = json['funcName'];
    obj.id = json['id'];
    obj.meta = json['meta'];
    obj.origin = json['origin'];
    obj.result = json['result'];
    obj.resultTTL = json['resultTTL'];
    obj.startedAt = json['startedAt'];
    obj.status = json['status'];
    obj.timeout = json['timeout'];
    obj.ttl = json['ttl'];
    
  return obj;
}
export function serializeJob(obj: Job, unroll=false): any {
  const json: any = {};
  json['dependson'] = obj.dependson
      json['description'] = obj.description
      json['endedAt'] = obj.endedAt
      json['enqueuedAt'] = obj.enqueuedAt
      json['excInfo'] = obj.excInfo
      json['failureTTL'] = obj.failureTTL
      json['funcName'] = obj.funcName
      json['id'] = obj.id
      json['meta'] = obj.meta
      json['origin'] = obj.origin
      json['result'] = obj.result
      json['resultTTL'] = obj.resultTTL
      json['startedAt'] = obj.startedAt
      json['status'] = obj.status
      json['timeout'] = obj.timeout
      json['ttl'] = obj.ttl
      
  return json;
}

export { Job };


class LdapStatus {
  public config!: object
  public status!: string
  
}

export function plainToLdapStatus(json: any): LdapStatus {
  const obj = new LdapStatus();
  obj.config = json['config'];
    obj.status = json['status'];
    
  return obj;
}
export function serializeLdapStatus(obj: LdapStatus, unroll=false): any {
  const json: any = {};
  json['config'] = obj.config
      json['status'] = obj.status
      
  return json;
}

export { LdapStatus };


class LdapPing {
  public error!: string
  public status!: string
  
}

export function plainToLdapPing(json: any): LdapPing {
  const obj = new LdapPing();
  obj.error = json['error'];
    obj.status = json['status'];
    
  return obj;
}
export function serializeLdapPing(obj: LdapPing, unroll=false): any {
  const json: any = {};
  json['error'] = obj.error
      json['status'] = obj.status
      
  return json;
}

export { LdapPing };


export interface AdmLdapSyncResults {
  job: number;
  started: Date | null;
  finished: Date | null;
  synced: string[];
  conflict: string[];
  failed: string[];
}
export function plainToAdmLdapSyncResults(json: any): AdmLdapSyncResults {
  return {
    job: json['job'],
    started: json['started'] ? new Date(json['started']) : null,
    finished: json['finished'] ? new Date(json['finished']) : null,
    synced: json['synced'],
    conflict: json['conflict'],
    failed: json['failed'],
  };
}

export interface AdmKey {
  key: string;
  val: AdmLdapSyncResults;
}


export interface Upload {
  tags: string[];
  container: Container;
}

export function plainToUpload(json: any): Upload {
  return {
    tags: json.tags,
    container: plainToContainer(json.container),
  };
}

export interface UserQuery {
  username?: string;
}

export interface SearchQuery {
  name?: string;
  description?: string;
}

export interface SearchResult {
  entity: Entity[];
  collection: Collection[];
  container: Container[];
  image: Image[];
}

export function plainToSearchResult(json: any): SearchResult {
  return {
    entity: _map(json.entity, plainToEntity),
    collection: _map(json.collection, plainToCollection),
    container: _map(json.container, plainToContainer),
    image: _map(json.image, plainToImage),
  };
}