{% import '_util.ts.tpl' as utils %}

import { getEnv } from '@/util/env';

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get path(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}`
  }

  public pullCmd(tag: string): string {
    const backend = (getEnv('VUE_APP_BACKEND_URL') as string).replace(/^https?:\/\//, '');
    const hasHttps = (getEnv('VUE_APP_BACKEND_URL') as string).startsWith('https');
    switch(this.type) {
      case('singularity'):
        return `singularity pull oras://${backend}${this.path}:${tag}`
      case('docker'):
      case('oci'):
        return `docker pull ${backend}${this.path}:${tag}`
      case('oras'):
        return `oras pull ${hasHttps ? '' : '--plain-http '}${backend}${this.path}:${tag}`
      default:
        return `curl something`
    }
  }
}

export function plainTo{{classname}}(json: any): {{classname}} {
  const obj = new {{classname}}();
  {{utils.deserialize(fields)}}
  return obj;
}
export function serialize{{classname}}(obj: {{classname}}, unroll=false): any {
  const json: any = {};
  {{utils.serialize(fields)}}
  return json;
}

export { {{classname}} };