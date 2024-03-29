// autogenerated with `swagspotta`, do not edit directly.
import { isNil as _isNil, map as _map, extend as _extend } from 'lodash';
import { prettyBytes, unPrettyBytes } from '@/util/pretty';

// IsLibraryPushRef returns true if the provided string is a valid library
// reference for a push operation.
// taken from scs-library-client src/client/util.go
// see https://github.com/sylabs/scs-library-client/blob/master/client/util.go#L36
export function isRefPart(name: string): boolean {
  const re = new RegExp("^[a-z0-9]+(?:[._-][a-z0-9]+)*$");
  return re.test(name);
}
export function checkName(name: string): boolean | string {
  return isRefPart(name) ? true :
    'Invalid name: can only contain lower case characters, numbers, -, _ or .'
}



class Collection {
  public canEdit!: boolean
  public containers!: string[]
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
  public usedQuota!: number
  

  public get collectionName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}/${this.name}`
  }
  public get prettyPath(): string {
    return this.fullPath;
  }
  
}

export function plainToCollection(json: any): Collection {
  const obj = new Collection();
  obj.canEdit = json['canEdit'];
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
      obj.usedQuota = json['usedQuota'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeCollection(obj: Collection, unroll=false): any {
  const json: any = {};
  json['createdBy'] = obj.createdBy;
      json['customData'] = obj.customData;
      json['description'] = obj.description;
      json['entity'] = obj.entity;
      json['name'] = obj.name;
      json['private'] = obj.private;
      
  return json;
}


export { Collection };


class Container {
  public archTags!: any
  public canEdit!: boolean
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
  public imageTags!: any
  public images!: string[]
  public name!: string
  public private!: boolean
  public readOnly!: boolean
  public size!: number
  public stars!: number
  public type!: string
  public updatedAt!: Date | null
  public usedQuota!: number
  public vcsUrl!: string
  

  public get containerName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}/${this.collectionName}/${this.name}`
  }
  public get prettyPath(): string {
    return this.fullPath;
  }

}

export function plainToContainer(json: any): Container {
  const obj = new Container();
  obj.archTags = json['archTags'];
    obj.canEdit = json['canEdit'];
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
    obj.type = json['type'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.usedQuota = json['usedQuota'];
    obj.vcsUrl = json['vcsUrl'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeContainer(obj: Container, unroll=false): any {
  const json: any = {};
  json['collection'] = obj.collection;
      json['createdBy'] = obj.createdBy;
      json['customData'] = obj.customData;
      json['description'] = obj.description;
      json['fullDescription'] = obj.fullDescription;
      json['name'] = obj.name;
      json['private'] = obj.private;
      json['readOnly'] = obj.readOnly;
      json['vcsUrl'] = obj.vcsUrl;
      
  return json;
}


export { Container };


class Entity {
  public canEdit!: boolean
  public collections!: string[]
  public createdAt!: Date | null
  public createdBy!: string
  public customData!: string
  public defaultPrivate!: boolean
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public groupRef!: string
  public id!: string
  public isGroup!: boolean
  public name!: string
  public quota!: number
  public size!: number
  public updatedAt!: Date | null
  public usedQuota!: number
  

  public get entityName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}`
  }
  public get prettyPath(): string {
    return this.fullPath;
  }

  public get prettyQuota(): string {
    return prettyBytes(this.quota);
  }
  public set prettyQuota(quota: string) {
    this.quota = unPrettyBytes(quota);
  }
  
}

export function plainToEntity(json: any): Entity {
  const obj = new Entity();
  obj.canEdit = json['canEdit'];
    obj.collections = json['collections'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.customData = json['customData'];
    obj.defaultPrivate = json['defaultPrivate'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.groupRef = json['groupRef'];
    obj.id = json['id'];
    obj.isGroup = json['isGroup'];
    obj.name = json['name'];
    obj.quota = json['quota'];
    obj.size = json['size'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.usedQuota = json['usedQuota'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeEntity(obj: Entity, unroll=false): any {
  const json: any = {};
  json['createdBy'] = obj.createdBy;
      json['customData'] = obj.customData;
      json['defaultPrivate'] = obj.defaultPrivate;
      json['description'] = obj.description;
      json['name'] = obj.name;
      
  return json;
}


export { Entity };


import { libraryUrl } from '@/util/pullCmds';

class Image {
  public arch!: string
  public blob!: string
  public canEdit!: boolean
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
  public encrypted!: boolean
  public entity!: string
  public entityName!: string
  public expiresAt!: Date | null
  public fingerprints!: string[]
  public hash!: string
  public id!: string
  public signatureVerified!: boolean
  public signed!: boolean
  public size!: number
  public tags!: string[]
  public type!: string
  public updatedAt!: Date | null
  public uploadState!: string
  

  public get path(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}`
  }

  public get fullPath(): string {
    return `${this.path}:${this.hash}`
  }
  public get prettyPath(): string {
    return `${this.path}:${this.tags.length>0 ? this.tags.join(",") : this.hash}`
  }

  public pullUrl(tag: string) {
    return libraryUrl(this, tag);
  }
}

export function plainToImage(json: any): Image {
  const obj = new Image();
  obj.arch = json['arch'];
    obj.blob = json['blob'];
    obj.canEdit = json['canEdit'];
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
    obj.encrypted = json['encrypted'];
    obj.entity = json['entity'];
    obj.entityName = json['entityName'];
    obj.expiresAt = _isNil(json['expiresAt']) ? null : new Date(json['expiresAt']);
      obj.fingerprints = json['fingerprints'];
    obj.hash = json['hash'];
    obj.id = json['id'];
    obj.signatureVerified = json['signatureVerified'];
    obj.signed = json['signed'];
    obj.size = json['size'];
    obj.tags = json['tags'];
    obj.type = json['type'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.uploadState = json['uploadState'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeImage(obj: Image, unroll=false): any {
  const json: any = {};
  json['arch'] = obj.arch;
      json['blob'] = obj.blob;
      json['container'] = obj.container;
      json['customData'] = obj.customData;
      json['description'] = obj.description;
      json['encrypted'] = obj.encrypted;
      json['expiresAt'] = _isNil(obj.expiresAt) ? null : obj.expiresAt.toJSON();
        json['hash'] = obj.hash;
      json['uploadState'] = obj.uploadState;
      
  return json;
}

export interface InspectAttributes {
  deffile: string;
}

export { Image };


class User {
  public canEdit!: boolean
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public email!: string
  public firstname!: string
  public id!: string
  public image_count!: number
  public isActive!: boolean
  public isAdmin!: boolean
  public lastname!: string
  public passwordDisabled!: boolean
  public quota!: number
  public source!: string
  public updatedAt!: Date | null
  public used_quota!: number
  public username!: string
  

  public password?: string
  public oldPassword?: string

  public get fullname(): string {
    return `${this.firstname} ${this.lastname}`;
  }

  public get role(): 'admin' | 'user' {
    return this.isAdmin ? 'admin' : 'user';
  }

  public stars: Container[] = []

  public get prettyQuota(): string {
    return prettyBytes(this.quota);
  }
  public set prettyQuota(quota: string) {
    this.quota = unPrettyBytes(quota);
  }
}

export function plainToUser(json: any): User {
  const obj = new User();
  obj.canEdit = json['canEdit'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.email = json['email'];
    obj.firstname = json['firstname'];
    obj.id = json['id'];
    obj.image_count = json['image_count'];
    obj.isActive = json['isActive'];
    obj.isAdmin = json['isAdmin'];
    obj.lastname = json['lastname'];
    obj.passwordDisabled = json['passwordDisabled'];
    obj.quota = json['quota'];
    obj.source = json['source'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.used_quota = json['used_quota'];
    obj.username = json['username'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeUser(obj: User, unroll=false): any {
  const json: any = {};
  json['email'] = obj.email;
      json['firstname'] = obj.firstname;
      json['isActive'] = obj.isActive;
      json['isAdmin'] = obj.isAdmin;
      json['lastname'] = obj.lastname;
      json['passwordDisabled'] = obj.passwordDisabled;
      json['quota'] = obj.quota;
      json['source'] = obj.source;
      json['username'] = obj.username;
      
  if (obj.password) {
    json['password']=obj.password;
  }
  if (obj.oldPassword) {
    json['oldPassword']=obj.oldPassword;
  }
  return json;
}

export { User };


export enum GroupRoles {
  admin = 'admin',
  contributor = 'contributor',
  readonly = 'readonly',
}

import { find as _find } from 'lodash';
class Group {
  public canEdit!: boolean
  public collections!: number
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public description!: string
  public email!: string
  public entityRef!: string
  public id!: string
  public image_count!: number
  public name!: string
  public quota!: number
  public updatedAt!: Date | null
  public used_quota!: number
  public users!: GroupMember[]
  

  public getRole(user: User | null): string | null {
    if (!user) {
      return null;
    }
    const member = _find(this.users, ug => ug.user.username === user.username);
    return !member ? null : member.role;
  }

  public get prettyQuota(): string {
    return prettyBytes(this.quota);
  }
  public set prettyQuota(quota: string) {
    this.quota = unPrettyBytes(quota);
  }

}

export function plainToGroup(json: any): Group {
  const obj = new Group();
  obj.canEdit = json['canEdit'];
    obj.collections = json['collections'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.deleted = json['deleted'];
    obj.deletedAt = _isNil(json['deletedAt']) ? null : new Date(json['deletedAt']);
      obj.description = json['description'];
    obj.email = json['email'];
    obj.entityRef = json['entityRef'];
    obj.id = json['id'];
    obj.image_count = json['image_count'];
    obj.name = json['name'];
    obj.quota = json['quota'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      obj.used_quota = json['used_quota'];
    if (!_isNil(json['users'])) obj.users = _map(json['users'], plainToGroupMember);
      
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeGroup(obj: Group, unroll=false): any {
  const json: any = {};
  json['createdBy'] = obj.createdBy;
      json['description'] = obj.description;
      json['email'] = obj.email;
      json['name'] = obj.name;
      json['quota'] = obj.quota;
      
  return json;
}

export { Group };


class GroupMember {
  public role!: string
  public user!: User
  
}

export function plainToGroupMember(json: any): GroupMember {
  const obj = new GroupMember();
  obj.role = json['role'];
    if (!_isNil(json['user'])) obj.user = plainToUser(json['user']);
      
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeGroupMember(obj: GroupMember, unroll=false): any {
  const json: any = {};
  json['role'] = obj.role;
      if (unroll) json['user'] = _isNil(obj.user) ? null : serializeUser(obj.user);
        
  return json;
}

export { GroupMember };


class Token {
  public comment!: string
  public createdAt!: Date | null
  public createdBy!: string
  public deleted!: boolean
  public deletedAt!: Date | null
  public expiresAt!: Date | null
  public generatedToken!: string
  public id!: string
  public key_uid!: string
  public source!: string
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
      obj.generatedToken = json['generatedToken'];
    obj.id = json['id'];
    obj.key_uid = json['key_uid'];
    obj.source = json['source'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      if (!_isNil(json['user'])) obj.user = plainToUser(json['user']);
      
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeToken(obj: Token, unroll=false): any {
  const json: any = {};
  json['comment'] = obj.comment;
      json['expiresAt'] = _isNil(obj.expiresAt) ? null : obj.expiresAt.toJSON();
        if (unroll) json['user'] = _isNil(obj.user) ? null : serializeUser(obj.user);
        
  return json;
}

export { Token };


class Job {
  public dependson!: string
  public description!: string
  public endedAt!: Date | null
  public enqueuedAt!: Date | null
  public excInfo!: string
  public failureTTL!: number
  public funcName!: string
  public id!: string
  public meta!: any
  public origin!: string
  public result!: string
  public resultTTL!: number
  public startedAt!: Date | null
  public status!: string
  public timeout!: string
  public ttl!: number
  
}

export function plainToJob(json: any): Job {
  const obj = new Job();
  obj.dependson = json['dependson'];
    obj.description = json['description'];
    obj.endedAt = _isNil(json['endedAt']) ? null : new Date(json['endedAt']);
      obj.enqueuedAt = _isNil(json['enqueuedAt']) ? null : new Date(json['enqueuedAt']);
      obj.excInfo = json['excInfo'];
    obj.failureTTL = json['failureTTL'];
    obj.funcName = json['funcName'];
    obj.id = json['id'];
    obj.meta = json['meta'];
    obj.origin = json['origin'];
    obj.result = json['result'];
    obj.resultTTL = json['resultTTL'];
    obj.startedAt = _isNil(json['startedAt']) ? null : new Date(json['startedAt']);
      obj.status = json['status'];
    obj.timeout = json['timeout'];
    obj.ttl = json['ttl'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeJob(obj: Job, unroll=false): any {
  const json: any = {};
  json['dependson'] = obj.dependson;
      json['description'] = obj.description;
      json['endedAt'] = _isNil(obj.endedAt) ? null : obj.endedAt.toJSON();
        json['enqueuedAt'] = _isNil(obj.enqueuedAt) ? null : obj.enqueuedAt.toJSON();
        json['excInfo'] = obj.excInfo;
      json['failureTTL'] = obj.failureTTL;
      json['funcName'] = obj.funcName;
      json['id'] = obj.id;
      json['meta'] = obj.meta;
      json['origin'] = obj.origin;
      json['result'] = obj.result;
      json['resultTTL'] = obj.resultTTL;
      json['startedAt'] = _isNil(obj.startedAt) ? null : obj.startedAt.toJSON();
        json['status'] = obj.status;
      json['timeout'] = obj.timeout;
      json['ttl'] = obj.ttl;
      
  return json;
}

export { Job };


class LdapStatus {
  public config!: any
  public status!: string
  
}

export function plainToLdapStatus(json: any): LdapStatus {
  const obj = new LdapStatus();
  obj.config = json['config'];
    obj.status = json['status'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeLdapStatus(obj: LdapStatus, unroll=false): any {
  const json: any = {};
  json['config'] = obj.config;
      json['status'] = obj.status;
      
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
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeLdapPing(obj: LdapPing, unroll=false): any {
  const json: any = {};
  json['error'] = obj.error;
      json['status'] = obj.status;
      
  return json;
}

export { LdapPing };


import { pullCmd } from '@/util/pullCmds';

class Manifest {
  public collection!: string
  public collectionName!: string
  public container!: string
  public containerName!: string
  public content!: any
  public createdAt!: Date | null
  public createdBy!: string
  public downloadCount!: number
  public entity!: string
  public entityName!: string
  public filename!: string
  public hash!: string
  public id!: string
  public images!: string[]
  public tags!: string[]
  public total_size!: number
  public type!: string
  public updatedAt!: Date | null
  

  public get path(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}`
  }

  public pullCmd(tag: string): string {
    return pullCmd(this, tag);
  }

 
}

export function plainToManifest(json: any): Manifest {
  const obj = new Manifest();
  obj.collection = json['collection'];
    obj.collectionName = json['collectionName'];
    obj.container = json['container'];
    obj.containerName = json['containerName'];
    obj.content = json['content'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.createdBy = json['createdBy'];
    obj.downloadCount = json['downloadCount'];
    obj.entity = json['entity'];
    obj.entityName = json['entityName'];
    obj.filename = json['filename'];
    obj.hash = json['hash'];
    obj.id = json['id'];
    obj.images = json['images'];
    obj.tags = json['tags'];
    obj.total_size = json['total_size'];
    obj.type = json['type'];
    obj.updatedAt = _isNil(json['updatedAt']) ? null : new Date(json['updatedAt']);
      
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeManifest(obj: Manifest, unroll=false): any {
  const json: any = {};
  json['collection'] = obj.collection;
      json['container'] = obj.container;
      json['content'] = obj.content;
      json['entity'] = obj.entity;
      json['hash'] = obj.hash;
      
  return json;
}

export { Manifest };


class ConfigParams {
  public default_group_quota!: number
  public default_user_quota!: number
  public enable_register!: boolean
  public frontend_url!: string
  public singularity_flavor!: string
  
}

export function plainToConfigParams(json: any): ConfigParams {
  const obj = new ConfigParams();
  obj.default_group_quota = json['default_group_quota'];
    obj.default_user_quota = json['default_user_quota'];
    obj.enable_register = json['enable_register'];
    obj.frontend_url = json['frontend_url'];
    obj.singularity_flavor = json['singularity_flavor'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializeConfigParams(obj: ConfigParams, unroll=false): any {
  const json: any = {};
  json['default_group_quota'] = obj.default_group_quota;
      json['default_user_quota'] = obj.default_user_quota;
      json['enable_register'] = obj.enable_register;
      json['frontend_url'] = obj.frontend_url;
      json['singularity_flavor'] = obj.singularity_flavor;
      
  return json;
}

export { ConfigParams };


class PassKey {
  public backed_up!: boolean
  public createdAt!: Date | null
  public current_sign_count!: number
  public id!: string
  public last_used!: Date | null
  public login_count!: number
  public name!: string
  
}

export function plainToPassKey(json: any): PassKey {
  const obj = new PassKey();
  obj.backed_up = json['backed_up'];
    obj.createdAt = _isNil(json['createdAt']) ? null : new Date(json['createdAt']);
      obj.current_sign_count = json['current_sign_count'];
    obj.id = json['id'];
    obj.last_used = _isNil(json['last_used']) ? null : new Date(json['last_used']);
      obj.login_count = json['login_count'];
    obj.name = json['name'];
    
  return obj;
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function serializePassKey(obj: PassKey, unroll=false): any {
  const json: any = {};
  json['name'] = obj.name;
      
  return json;
}

export { PassKey };


interface AdmBase {
  job: number;
  started: Date | null;
  finished: Date | null;
  success: boolean;
  exception: string;
  scheduled: Date | null;
}

export interface AdmLdapSyncResults extends AdmBase {
  synced: string[];
  conflict: string[];
  failed: string[];
}

export interface AdmExpireImagesResults extends AdmBase {
  updated: number;
  space_reclaimed: number;
}

export interface AdmUpdateQuotasResults extends AdmBase {
  updated: number;
  total_space: number;
}

function plainToAdmBase(json: any): AdmBase {
  return {
    job: json['job'],
    started: json['started'] ? new Date(json['started']) : null,
    finished: json['finished'] ? new Date(json['finished']) : null,
    success: json['success'],
    exception: json['exception'],
    scheduled: json['scheduled'] ? new Date(json['scheduled']) : null,
  }
}

export function plainToAdmLdapSyncResults(json: any): AdmLdapSyncResults {
  return _extend(plainToAdmBase(json), {
    synced: json['synced'],
    conflict: json['conflict'],
    failed: json['failed'],
  });
}

export function plainToAdmExpireImagesResults(json: any): AdmExpireImagesResults {
  return _extend(plainToAdmBase(json), {
    updated: json['updated'],
    space_reclaimed: json['space_reclaimed'],
  });
}

export function plainToAdmUpdateQuotasResults(json: any): AdmUpdateQuotasResults {
  return _extend(plainToAdmBase(json), {
    updated: json['updated'],
    total_space: json['total_space'],
  });
}

export interface AdmKey {
  key: string;
  val: AdmLdapSyncResults;
}


export interface UploadTag {
  name: string;
  arch: string;
  imageType: string;
  manifestType: string;
}

export interface Upload {
  tags: UploadTag[];
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
