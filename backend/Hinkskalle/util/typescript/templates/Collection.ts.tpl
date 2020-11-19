{% import '_util.ts.tpl' as utils %}

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get collectionName(): string {
    return this.name;
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