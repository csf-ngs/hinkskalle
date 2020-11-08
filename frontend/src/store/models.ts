import { isEmpty as _isEmpty, isNil as _isNil, map as _map, each as _each, filter as _filter, keyBy as _keyBy, concat as _concat, every as _every } from 'lodash';



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
  json['customData'] = obj.customData
      json['description'] = obj.description
      json['entity'] = obj.entity
      json['name'] = obj.name
      json['private'] = obj.private
      
  return json;
}

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
  
}

export { Collection };


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
      json['customData'] = obj.customData
      json['description'] = obj.description
      json['fullDescription'] = obj.fullDescription
      json['name'] = obj.name
      json['private'] = obj.private
      json['readOnly'] = obj.readOnly
      json['vcsUrl'] = obj.vcsUrl
      
  return json;
}

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
  
}

export { Container };


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
  json['customData'] = obj.customData
      json['defaultPrivate'] = obj.defaultPrivate
      json['description'] = obj.description
      json['name'] = obj.name
      
  return json;
}

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
  
}

export { Entity };


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
  
}

export { Image };


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
      
  return json;
}

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
  
}

export { User };


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

export { Group };
