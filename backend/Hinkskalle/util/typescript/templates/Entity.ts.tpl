{% import '_util.ts.tpl' as utils %}

import { prettyBytes, unPrettyBytes } from '@/util/pretty';
class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get entityName(): string {
    return this.name;
  }
  public get fullPath(): string {
    return `${this.entityName}`
  }
  public get prettyPath(): string {
    return this.fullPath;
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }

  public get prettyQuota(): string {
    return prettyBytes(this.quota);
  }
  public set prettyQuota(quota: string) {
    this.quota = unPrettyBytes(quota);
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