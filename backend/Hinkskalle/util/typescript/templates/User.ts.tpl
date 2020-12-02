{% import '_util.ts.tpl' as utils %}

class {{classname}} {
  {{utils.auto_attributes(fields)}}

  public password?: string

  public get fullname(): string {
    return `${this.firstname} ${this.lastname}`;
  }

  public get role(): 'admin' | 'user' {
    return this.isAdmin ? 'admin' : 'user';
  }

  public canEdit(user: User | null): boolean {
    return !!user && (user.isAdmin || this.username===user.username);
  }

  public stars: Container[] = []
}

export function plainTo{{classname}}(json: any): {{classname}} {
  const obj = new {{classname}}();
  {{utils.deserialize(fields)}}
  return obj;
}
export function serialize{{classname}}(obj: {{classname}}, unroll=false): any {
  const json: any = {};
  {{utils.serialize(fields)}}
  if (obj.password) {
    json['password']=obj.password;
  }
  return json;
}

export { {{classname}} };