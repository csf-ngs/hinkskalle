from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.models.User import GroupRoles
from Hinkskalle.util.auth.token import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from marshmallow import fields, Schema, EXCLUDE
from flask import g
from sqlalchemy.exc import IntegrityError, NoResultFound
from slugify import slugify

from Hinkskalle.models import GroupSchema, Group, UserGroup, Entity, User


class GroupResponseSchema(ResponseSchema):
    data = fields.Nested(GroupSchema)


class GroupListResponseSchema(ResponseSchema):
    data = fields.Nested(GroupSchema, many=True)


class GroupSearchQuerySchema(RequestSchema):
    name = fields.String(required=False)


class GroupCreateSchema(GroupSchema, RequestSchema):
    pass


class GroupUpdateSchema(GroupSchema, RequestSchema):
    name = fields.String(required=False)


class GroupDeleteResponseSchema(ResponseSchema):
    status = fields.String()


class MemberSchema(Schema):
    username = fields.String(required=True)
    id = fields.String(dump_only=True)
    email = fields.String(dump_only=True)
    firstname = fields.String(dump_only=True)
    lastname = fields.String(dump_only=True)
    is_active = fields.Boolean(data_key="isActive", dump_only=True)
    is_admin = fields.Boolean(data_key="isAdmin", dump_only=True)

    class Meta:
        unknown = EXCLUDE


class LGroupMemberSchema(Schema):
    role = fields.String(required=True)
    user = fields.Nested(MemberSchema)


class GroupMembersResponseSchema(ResponseSchema):
    data = fields.Nested(LGroupMemberSchema, many=True)


@registry.handles(
    rule="/v1/groups",
    method="GET",
    response_body_schema=GroupListResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    query_string_schema=GroupSearchQuerySchema(),
    tags=["hinkskalle-ext"],
)
def list_groups():
    args = rebar.validated_args
    search = []
    if not g.authenticated_user.is_admin:
        search.append(UserGroup.user_id == g.authenticated_user.id)
    if args.get("name", None):
        search.append(Group.name.ilike(f"%{args['name']}%"))
    objs = Group.query.outerjoin(Group.users).filter(*search).order_by(Group.name)
    return {"data": list(objs)}


@registry.handles(
    rule="/v1/groups/<string:name>",
    method="GET",
    response_body_schema=GroupResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    tags=["hinkskalle-ext"],
)
def get_group(name):
    try:
        group = Group.query.filter(Group.name == name).one()
    except NoResultFound:
        raise errors.NotFound(f"group {name} not found")
    if not group.check_access(g.authenticated_user):
        raise errors.Forbidden("Access denied to group.")
    return {"data": group}


@registry.handles(
    rule="/v1/groups",
    method="POST",
    request_body_schema=GroupCreateSchema(),
    response_body_schema=GroupResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    tags=["hinkskalle-ext"],
)
def create_group():
    body = rebar.validated_body
    body.pop("id", None)

    # users cannot set group quotas
    if not g.authenticated_user.is_admin:
        body.pop("quota", None)

    new_group = Group(**body)

    new_group.createdBy = g.authenticated_user.username
    ug = UserGroup(user=g.authenticated_user, group=new_group, role=GroupRoles.admin)

    entity = Entity(name=slugify(new_group.name), owner=g.authenticated_user, group=new_group)
    try:
        db.session.add(new_group)
        db.session.add(entity)
        db.session.commit()
    except IntegrityError as err:
        msg = (
            f"Group {new_group.name} already exists"
            if err.statement.find("entity") == -1
            else f"entity {new_group.name} already exists"
        )
        raise errors.PreconditionFailed(msg)

    return {"data": new_group}


@registry.handles(
    rule="/v1/groups/<string:name>",
    method="PUT",
    request_body_schema=GroupUpdateSchema(),
    response_body_schema=GroupResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    tags=["hinkskalle-ext"],
)
def update_group(name: str):
    body = rebar.validated_body

    try:
        group: Group = Group.query.filter(Group.name == name).one()
    except NoResultFound:
        raise errors.NotFound(f"group {name} not found")

    if not group.check_update_access(g.authenticated_user):
        raise errors.Forbidden(f"no access to group {name}")

    if not g.authenticated_user.is_admin:
        body.pop("quota", None)

    for key in body:
        setattr(group, key, body[key])

    with db.session.no_autoflush:  # type: ignore
        if name != group.name and group.entity is not None:
            group.entity.name = slugify(group.name)

    try:
        db.session.commit()
    except IntegrityError as err:
        raise errors.Conflict(f"Cannot change group name, new name already taken")

    return {"data": group}


@registry.handles(
    rule="/v1/groups/<string:name>/members",
    method="PUT",
    request_body_schema=LGroupMemberSchema(many=True),
    response_body_schema=GroupMembersResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    tags=["hinkskalle-ext"],
)
def update_members(name: str):
    body = rebar.validated_body

    try:
        group: Group = Group.query.filter(Group.name == name).one()
    except NoResultFound:
        raise errors.NotFound(f"group {name} not found")

    if not group.check_update_access(g.authenticated_user):
        raise errors.Forbidden(f"no access to group {name}")

    current = {ug.user.username: ug for ug in group.users}
    should = {ug["user"]["username"]: ug for ug in body}

    for (username, ug) in current.items():
        if username in should:
            ug.role = should[username]["role"]
            should.pop(username)
        else:
            db.session.delete(ug)

    for (username, ug) in should.items():
        try:
            user = User.query.filter(User.username == username).one()
        except NoResultFound:
            raise errors.NotFound(f"user {username} does not exist")
        ug = UserGroup(user=user, group=group, role=ug["role"])
        db.session.add(ug)

    db.session.commit()
    return {"data": group.users}


@registry.handles(
    rule="/v1/groups/<string:name>",
    method="DELETE",
    response_body_schema=GroupDeleteResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.user),  # type: ignore
    tags=["hinkskalle-ext"],
)
def delete_group(name):
    try:
        group: Group = Group.query.filter(Group.name == name).one()
    except NoResultFound:
        raise errors.NotFound(f"group {name} not found")

    if not group.check_update_access(g.authenticated_user):
        raise errors.Forbidden(f"no access to group {name}")

    try:
        db.session.delete(group)
        db.session.commit()
    except IntegrityError:
        raise errors.PreconditionFailed(f"Cannot delete, entity not empty")

    return {"status": "ok"}
