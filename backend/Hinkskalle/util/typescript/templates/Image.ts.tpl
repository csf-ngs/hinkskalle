{% import '_util.ts.tpl' as utils %}

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get fullPath(): string {
    return `${this.entityName}/${this.collectionName}/${this.containerName}:${this.hash}`
  }

  public canEdit(user: User | null): boolean {
    return !!user && this.createdBy===user.username;
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