{% import '_util.ts.tpl' as utils %}

import { libraryUrl } from '@/util/pullCmds';

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get path(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}`
  }

  public get fullPath(): string {
    return `${this.path}:${this.hash}`
  }
  public get prettyPath(): string {
    return `${this.path}:${this.tags.length>0 ? this.tags.join(",") : this.hash}`
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.createdBy===user.username);
  }

  public pullUrl(tag: string) {
    return libraryUrl(this, tag);
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

export interface InspectAttributes {
  deffile: string;
}

export { {{classname}} };