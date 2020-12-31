// autogenerated with `flask create-typescript-models`, do not edit directly.
import { isNil as _isNil, map as _map } from 'lodash';

{% for model in models -%}
{{model}}
{% endfor %}

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