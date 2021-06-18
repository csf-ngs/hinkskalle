{% import '_util.ts.tpl' as utils %}

import { pullCmd } from '@/util/pullCmds';

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get path(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}`
  }

  public pullCmd(tag: string): string {
    return pullCmd(this, tag);
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