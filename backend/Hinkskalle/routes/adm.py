from flask import current_app
from Hinkskalle import registry, rebar, authenticator, db
from Hinkskalle.util.auth.token import Scopes

from flask_rebar import RequestSchema, ResponseSchema, errors
from sqlalchemy.exc import IntegrityError

from marshmallow import fields, Schema

from Hinkskalle.models.Adm import AdmSchema, Adm, AdmKeys
from flask_rq2.job import Job
from ..util.schema import BaseSchema, LocalDateTime


class AdmResponseSchema(ResponseSchema):
    data = fields.Nested(AdmSchema)


class AdmUpdateSchema(AdmSchema, RequestSchema):
    pass


def _serialize_job(job: Job) -> dict:
    return {
        "id": job.id,
        "meta": job.meta,
        "origin": job.origin,
        "status": job.get_status(),
        "description": job.description,
        "dependson": ",".join(job.dependency_ids),
        "failureTTL": job.failure_ttl,
        "timeout": job.timeout,
        "result": job.result,
        "enqueuedAt": job.enqueued_at,
        "startedAt": job.started_at,
        "endedAt": job.ended_at,
        "excInfo": job.exc_info,
        "funcName": job.func_name,
    }


class JobSchema(BaseSchema):
    id = fields.String()
    meta = fields.Dict()
    origin = fields.String()
    status = fields.String()
    description = fields.String()
    dependson = fields.String()
    failureTTL = fields.Int(allow_none=True)
    ttl = fields.Int(allow_none=True)
    resultTTL = fields.Int()
    timeout = fields.String()
    result = fields.String(allow_none=True)
    enqueuedAt = LocalDateTime()
    startedAt = LocalDateTime(allow_none=True)
    endedAt = LocalDateTime(allow_none=True)
    excInfo = fields.String(allow_none=True)
    funcName = fields.String()


class JobResponseSchema(ResponseSchema):
    data = fields.Nested(JobSchema)


class LdapPingSchema(Schema):
    status = fields.String()
    error = fields.String()


class LdapStatusSchema(Schema):
    status = fields.String()
    config = fields.Dict()


class LdapPingResponseSchema(ResponseSchema):
    data = fields.Nested(LdapPingSchema)


class LdapStatusResponseSchema(ResponseSchema):
    data = fields.Nested(LdapStatusSchema)


@registry.handles(
    rule="/v1/adm/<string:key>",
    method="GET",
    response_body_schema=AdmResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def get_key(key):
    db_key: Adm = Adm.query.get(key)
    if not db_key:
        raise errors.NotFound(f"key {key} does not exist")

    from Hinkskalle.util.jobs import get_cron

    for j in get_cron():
        if j[0].id == f"cron-{key}":
            db_key.val["scheduled"] = j[1]

    return {"data": db_key}


@registry.handles(
    rule="/v1/adm/<string:key>",
    method="PUT",
    request_body_schema=AdmUpdateSchema(),
    response_body_schema=AdmResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def update_key(key):
    body = rebar.validated_body

    if key not in [k.name for k in AdmKeys]:
        raise errors.BadRequest(f"Invalid key")

    db_key = Adm.query.get(key)
    if not db_key:
        db_key = Adm(key=key)
        db.session.add(db_key)

    db_key.val = body.get("val")
    try:
        db.session.commit()
    except IntegrityError:
        raise errors.BadRequest(f"Invalid key")

    return {"data": db_key}


@registry.handles(
    rule="/v1/ldap/status",
    method="GET",
    response_body_schema=LdapStatusResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def ldap_status():
    from Hinkskalle.util.auth.ldap import LDAPUsers

    ret = {}
    try:
        ldap = LDAPUsers(app=current_app)
        if ldap.enabled:
            ret["status"] = "configured"
            ret["config"] = ldap.config.copy()
            ret["config"].pop("BIND_PASSWORD", "")
        else:
            ret["status"] = "disabled"
    except Exception:
        ret["status"] = "fail"

    return {"data": ret}


@registry.handles(
    rule="/v1/ldap/ping",
    method="GET",
    response_body_schema=LdapPingResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def ping_ldap():
    from Hinkskalle.util.auth.ldap import LDAPUsers

    ret = {}
    try:
        svc = LDAPUsers(app=current_app)
        if not svc.enabled:
            ret["status"] = "failed"
            ret["error"] = "LDAP not configured."
        else:
            svc.ldap.connect()
            ret["status"] = "ok"
    except Exception as err:
        ret["status"] = "failed"
        ret["error"] = str(err)
    return {"data": ret}


@registry.handles(
    rule="/v1/ldap/sync",
    method="POST",
    response_body_schema=JobResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def sync_ldap():
    """deprecated, use /v1/adm/ldap_sync_results/run"""
    return start_task(AdmKeys.ldap_sync_results.name)


@registry.handles(
    rule="/v1/adm/<string:key>/run",
    method="POST",
    response_body_schema=JobResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def start_task(key):
    from Hinkskalle.util.jobs import adm_map

    if key not in adm_map:
        raise errors.NotAcceptable(f"Invalid adm key {key}")
    job = adm_map[key].queue()
    return {"data": _serialize_job(job)}


@registry.handles(
    rule="/v1/jobs/<string:id>",
    method="GET",
    response_body_schema=JobResponseSchema(),
    authenticators=authenticator.with_scope(Scopes.admin),  # type: ignore
    tags=["admin"],
)
def get_job(id):
    from Hinkskalle.util.jobs import get_job_info

    job = get_job_info(id)
    if not job:
        raise errors.NotFound("job id not found")
    return {"data": _serialize_job(job)}
