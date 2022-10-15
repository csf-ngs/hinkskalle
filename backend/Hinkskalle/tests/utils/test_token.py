from Hinkskalle import db
from ..route_base import RouteBase
from .._util import _create_user

from flask_rebar import errors
from flask import g

from Hinkskalle.util.auth.token import TokenAuthenticator, Scopes
from Hinkskalle.models import Token


class TestTokenAuth(RouteBase):
    def test_header_ok(self):
        token_auth = TokenAuthenticator()
        with self.app.test_request_context("", headers={"Authorization": "Bearer Schokobanane"}):
            found = token_auth._get_token()
            self.assertEqual(found, "Schokobanane")

        with self.app.test_request_context("", headers={"Authorization": "Bearer  Schokobanane"}):
            found = token_auth._get_token()
            self.assertEqual(found, "Schokobanane")

        with self.app.test_request_context("", headers={"Authorization": "bEaReR Schokobanane"}):
            found = token_auth._get_token()
            self.assertEqual(found, "Schokobanane")

    def test_header_missing(self):
        token_auth = TokenAuthenticator()

        with self.assertRaises(errors.Unauthorized):
            with self.app.test_request_context("", headers={"Notorization": "bla bla"}):
                token_auth._get_token()

    def test_header_wrong_scheme(self):
        token_auth = TokenAuthenticator()

        with self.assertRaises(errors.NotAcceptable):
            with self.app.test_request_context("", headers={"Authorization": "bla bla"}):
                token_auth._get_token()

    def test_header_missing_token(self):
        token_auth = TokenAuthenticator()

        with self.assertRaises(errors.NotAcceptable):
            with self.app.test_request_context("", headers={"Authorization": "Bearer"}):
                token_auth._get_token()

        with self.assertRaises(errors.NotAcceptable):
            with self.app.test_request_context("", headers={"Authorization": "Bearer "}):
                token_auth._get_token()

    def test_header_invalid_token(self):
        token_auth = TokenAuthenticator()

        with self.assertRaises(errors.NotAcceptable):
            with self.app.test_request_context("", headers={"Authorization": "Bearer a b c"}):
                token_auth._get_token()

        with self.assertRaises(errors.NotAcceptable):
            with self.app.test_request_context("", headers={"Authorization": "Bearer "}):
                token_auth._get_token()

    def test_get_identity(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))
        db.session.commit()

        token_auth = TokenAuthenticator()
        identity = token_auth._get_identity("schoko-banane")

        self.assertEqual(identity.user.username, test_user.username)

    def test_get_identity_invalid(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="noko-schabane"))
        db.session.commit()

        token_auth = TokenAuthenticator()
        with self.assertRaises(errors.Unauthorized):
            token_auth._get_identity("schoko-banane")

    def test_get_identity_deactivated(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))
        test_user.is_active = False
        db.session.commit()

        token_auth = TokenAuthenticator()
        with self.assertRaises(errors.Unauthorized):
            token_auth._get_identity("schoko-banane")

    def test_authenticate(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))
        db.session.commit()

        token_auth = TokenAuthenticator()
        with self.app.test_request_context("", headers={"Authorization": "Bearer schoko-banane"}) as ctx:
            token_auth.authenticate()
            self.assertEqual(g.authenticated_user.username, test_user.username)

    def test_scoped_authenticator(self):
        scoped = TokenAuthenticator().with_scope(Scopes.admin)
        self.assertEqual(scoped.scope, Scopes.admin)

        scoped = TokenAuthenticator().with_scope(Scopes.user)
        self.assertEqual(scoped.scope, Scopes.user)

        scoped = TokenAuthenticator().with_scope(Scopes.optional)
        self.assertEqual(scoped.scope, Scopes.optional)

        with self.assertRaises(ValueError):
            scoped = TokenAuthenticator().with_scope("oink")  # type: ignore

    def test_scoped_optional(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))
        db.session.commit()

        scoped = TokenAuthenticator().with_scope(Scopes.optional)
        with self.app.test_request_context("") as ctx:
            scoped.authenticate()
            self.assertIsNone(g.authenticated_user)

        with self.app.test_request_context("", headers={"Authorization": "Bearer oink"}) as ctx:
            with self.assertRaises(errors.Unauthorized):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer schoko-banane"}) as ctx:
            scoped.authenticate()
            self.assertEqual(g.authenticated_user.username, test_user.username)

    def test_scoped_user(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))
        db.session.commit()

        scoped = TokenAuthenticator().with_scope(Scopes.user)
        with self.app.test_request_context("") as ctx:
            with self.assertRaises(errors.Unauthorized):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer oink"}) as ctx:
            with self.assertRaises(errors.Unauthorized):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer schoko-banane"}) as ctx:
            scoped.authenticate()
            self.assertEqual(g.authenticated_user.username, test_user.username)

    def test_scoped_admin(self):
        test_user = _create_user()
        test_user.tokens.append(Token(token="schoko-banane"))

        admin_user = _create_user(name="admin.fuchs", is_admin=True)
        admin_user.tokens.append(Token(token="admin-banane"))

        db.session.commit()

        scoped = TokenAuthenticator().with_scope(Scopes.admin)
        with self.app.test_request_context("") as ctx:
            with self.assertRaises(errors.Unauthorized):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer oink"}) as ctx:
            with self.assertRaises(errors.Unauthorized):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer schoko-banane"}) as ctx:
            with self.assertRaises(errors.Forbidden):
                scoped.authenticate()

        with self.app.test_request_context("", headers={"Authorization": "Bearer admin-banane"}) as ctx:
            scoped.authenticate()
            self.assertEqual(g.authenticated_user.username, admin_user.username)
