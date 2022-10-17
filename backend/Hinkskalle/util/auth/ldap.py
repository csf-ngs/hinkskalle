from .base import PasswordCheckerBase
from .exceptions import UserNotFound, InvalidPassword, UserConflict

from sqlalchemy.orm.exc import NoResultFound

from ldap3 import Server, Connection, SUBTREE, SYNC, SCHEMA
from ldap3.utils.conv import escape_filter_chars
from ldap3.core.exceptions import (
    LDAPInvalidCredentialsResult,
    LDAPPasswordIsMandatoryError,
    LDAPNoSuchObjectResult,
)

from slugify import slugify

from flask import current_app


# mock ldap returns scalar, real ldap (slapd) a list
# make sure we can deal with both
def _get_attr(attr):
    if type(attr) == list:
        return attr[0]
    else:
        return attr


class LDAPService:
    def __init__(
        self,
        host,
        base_dn,
        filter,
        all_users_filter,
        port=389,
        bind_dn=None,
        bind_password=None,
        get_info=SCHEMA,
        client_strategy=SYNC,
    ):
        self.host = host
        self.port = int(port) if port else None
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.base_dn = base_dn
        self.filter = filter
        self.all_users_filter = all_users_filter

        self.server = Server(host=self.host, port=self.port, get_info=get_info)  # type: ignore
        self.connection = Connection(self.server, self.bind_dn, self.bind_password, raise_exceptions=True, client_strategy=client_strategy)  # type: ignore

    def connect(self):
        self.connection.rebind(user=self.bind_dn, password=self.bind_password)

    def close(self):
        self.connection.unbind()

    def search_user(self, username: str):
        try:
            self.connection.search(
                search_base=self.base_dn,
                search_filter=self.filter.format(escape_filter_chars(username)),
                search_scope=SUBTREE,
                attributes="*",
            )
        except LDAPNoSuchObjectResult:
            raise UserNotFound()
        if self.connection.response is None:
            raise Exception("No response received.")
        elif len(self.connection.response) == 0:
            raise UserNotFound()
        return self.connection.response[0]

    def list_users(self):
        self.connection.search(
            search_base=self.base_dn, search_filter=self.all_users_filter, search_scope=SUBTREE, attributes="*"
        )
        # current_app.logger.debug(len(self.connection.response))
        if self.connection.response is None:
            raise Exception(f"no response received")
        return self.connection.response


class LDAPUsers(PasswordCheckerBase):
    default_attrmap = {
        "username": "uid",
        "email": "mail",
        "firstname": "givenName",
        "lastname": "sn",
    }
    default_filter = "(&(uid={})(objectClass=person))"
    default_all_users_filter = "(objectClass=person)"

    def __init__(self, app=None, svc=None):
        if app:
            self.app = app
        else:
            self.app = current_app
        self.config = self.app.config.get("AUTH", {}).get("LDAP", {})
        self.enabled = self.config.get("ENABLED", False)
        if not self.enabled and not svc:
            self.app.logger.debug(f"LDAP is not configured.")
            return

        if svc is None:
            self.app.logger.debug(f"initializing ldap service with host {self.config.get('HOST', '')}")
            self.ldap = LDAPService(
                host=self.config.get("HOST", ""),
                port=self.config.get("PORT", 389),
                bind_dn=self.config.get("BIND_DN"),
                bind_password=self.config.get("BIND_PASSWORD"),
                base_dn=self.config.get("BASE_DN"),
                filter=self.config.get("FILTERS", {}).get("user", self.default_filter),
                all_users_filter=self.config.get("FILTERS", {}).get("all_users", self.default_all_users_filter),
            )
        else:
            self.ldap = svc

        self.attrmap = self.config.get("ATTRIBUTES", {})
        for (k, v) in self.default_attrmap.items():
            if self.attrmap.get(k) is None:
                self.attrmap[k] = v

        self.username_attr = self.attrmap.get("username")
        self.attrmap.pop("username")

    def sync_user(self, entry):
        from Hinkskalle.models.User import User
        from Hinkskalle.models.Entity import Entity
        from Hinkskalle import db

        attrs = entry.get("attributes")
        try:
            user = User.query.filter(User.username == _get_attr(attrs.get(self.username_attr))).one()

            if not user.source == "ldap":
                raise UserConflict(username=user.username)

        except NoResultFound:
            user = User()
            user.is_admin = False
            user.is_active = True

        user.username = slugify(_get_attr(attrs.get(self.username_attr)), separator=".")
        for (k, v) in self.attrmap.items():
            setattr(user, k, _get_attr(attrs.get(v)))
        user.source = "ldap"

        db.session.add(user)
        db.session.commit()
        try:
            Entity.query.filter(Entity.name == user.username).one()
        except NoResultFound:
            entity = Entity(name=user.username, owner=user)
            db.session.add(entity)
            db.session.commit()

        return user

    def check_password(self, username: str, password: str):
        self.ldap.connect()
        ldap_user = self.ldap.search_user(username)
        try:
            self.ldap.connection.rebind(user=ldap_user.get("dn"), password=password)
        except (LDAPInvalidCredentialsResult, LDAPPasswordIsMandatoryError):
            raise InvalidPassword()
        self.ldap.close()

        db_user = self.sync_user(ldap_user)
        return db_user
