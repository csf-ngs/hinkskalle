{% import '_util.ts.tpl' as utils %}

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public get fullname(): string {
    return `${this.firstname} ${this.lastname}`;
  }

  public get role(): 'admin' | 'user' {
    return this.isAdmin ? 'admin' : 'user';
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