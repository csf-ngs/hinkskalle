import datetime
import typing
from flask import g, session
from ..route_base import RouteBase

from .._util import _create_user, _get_json_data
from Hinkskalle.models.User import Token, PassKey, User
from Hinkskalle.models.Entity import Entity
from Hinkskalle import db
from webauthn.helpers.base64url_to_bytes import base64url_to_bytes
import re
import jwt
import base64


class TestPasswordAuth(RouteBase):
    def test_password(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        db.session.commit()

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "supergeheim"})
            self.assertEqual(ret.status_code, 200)
            self.assertIn("authenticated_user", g)
            self.assertEqual(g.authenticated_user, user)

        data = _get_json_data(ret)
        self.assertIn("id", data)
        self.assertIn("generatedToken", data)
        self.assertIn("expiresAt", data)

        self.assertEqual(len(user.tokens), 1)
        db_token = Token.query.filter(Token.id == data["id"]).first()
        self.assertIsNotNone(db_token)
        self.assertEqual(db_token.source, "auto")
        self.assertTrue(
            abs(db_token.expiresAt - (datetime.datetime.now() + Token.defaultExpiration))
            < datetime.timedelta(minutes=1)
        )

    def test_password_disabled(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        user.password_disabled = True
        db.session.commit()

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "supergeheim"})
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.get("authenticated_user"))

    def test_login_entity_create(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        db.session.commit()

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "supergeheim"})
            self.assertEqual(ret.status_code, 200)
        db_entity = Entity.query.filter(Entity.name == "oink.hase").first()
        self.assertIsNotNone(db_entity)
        self.assertEqual(db_entity.createdBy, "oink.hase")

    def test_login_entity_exists(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        entity = Entity(name="oink.hase")
        db.session.add(entity)
        db.session.commit()
        entity_id = entity.id

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "supergeheim"})
            self.assertEqual(ret.status_code, 200)

    def test_password_fail(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        db.session.commit()

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "superfalsch"})
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.get("authenticated_user"))

    def test_password_user_not_found(self):
        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": "gits.net", "password": "superfalsch"})
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.get("authenticated_user"))

    def test_password_deactivated(self):
        user = _create_user(name="oink.hase")
        user.set_password("supergeheim")
        user.is_active = False
        db.session.commit()

        with self.app.test_client() as c:
            ret = c.post("/v1/get-token", json={"username": user.username, "password": "supergeheim"})
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.get("authenticated_user"))


class TestDownloadToken(RouteBase):
    def test_get_download_token(self):
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/get-download-token", json={"type": "manifest", "id": "1"})
        self.assertEqual(ret.status_code, 202)
        data = typing.cast(dict, ret.get_json())
        location = ret.headers.get("Location", "")
        self.assertTrue(location.endswith(data["location"]))
        temp_token = re.search(r"(.*)\?temp_token=(.*)", location)
        self.assertIsNotNone(temp_token)
        temp_token = typing.cast(re.Match, temp_token)
        self.assertIsNotNone(temp_token[1])
        self.assertTrue(temp_token[1].endswith("/manifests/1/download"))
        self.assertIsNotNone(temp_token[2])
        decoded = jwt.decode(temp_token[2], self.app.config["SECRET_KEY"], algorithms=["HS256"])
        self.assertEqual(decoded.get("id"), "1")
        self.assertEqual(decoded.get("type"), "manifest")
        self.assertEqual(decoded.get("username"), self.admin_username)
        self.assertLessEqual(decoded.get("exp"), int(datetime.datetime.now().timestamp() + self.app.config["DOWNLOAD_TOKEN_EXPIRATION"]))  # type: ignore
        self.assertGreaterEqual(decoded.get("exp"), int(datetime.datetime.now().timestamp() + self.app.config["DOWNLOAD_TOKEN_EXPIRATION"]))  # type: ignore

    def test_get_handout_token(self):
        override_exp = datetime.datetime.now().timestamp() + 120
        with self.fake_admin_auth():
            ret = self.client.post(
                f"/v1/get-download-token",
                json={"type": "manifest", "id": "1", "username": self.username, "exp": override_exp},
            )
        self.assertEqual(ret.status_code, 202)
        location = ret.headers.get("Location", "")
        self.assertTrue(location.endswith(typing.cast(dict, ret.get_json())["location"]))
        temp_token = re.search(r"(.*)\?temp_token=(.*)", location)
        self.assertIsNotNone(temp_token)
        temp_token = typing.cast(re.Match, temp_token)
        decoded = jwt.decode(temp_token[2], self.app.config["SECRET_KEY"], algorithms=["HS256"])

        self.assertEqual(decoded.get("username"), self.username)
        self.assertEqual(decoded.get("exp"), int(override_exp))

    # OINK:
    def test_get_download_token_user(self):
        with self.fake_auth():
            ret = self.client.post(f"/v1/get-download-token", json={"type": "manifest", "id": "1"})
        self.assertEqual(ret.status_code, 202)

    def test_get_download_token_user_no_override(self):
        with self.fake_auth():
            ret = self.client.post(
                f"/v1/get-download-token", json={"type": "manifest", "id": "1", "username": self.other_username}
            )
        self.assertEqual(ret.status_code, 403)

        with self.fake_auth():
            ret = self.client.post(f"/v1/get-download-token", json={"type": "manifest", "id": "1", "exp": 4711})
        self.assertEqual(ret.status_code, 403)

    def test_get_download_noauth(self):
        ret = self.client.post(f"/v1/get-download-token", json={"type": "manifest", "id": "1"})
        self.assertEqual(ret.status_code, 401)

    def test_get_download_token_invalid_type(self):
        with self.fake_admin_auth():
            ret = self.client.post(f"/v1/get-download-token", json={"type": "oink", "id": "1"})
        self.assertEqual(ret.status_code, 406)


class TestTokenAuth(RouteBase):
    def test_token_status_no_token(self):
        ret = self.client.get("/v1/token-status")
        self.assertEqual(ret.status_code, 401)

    def test_token_status(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        user.tokens.append(Token(token=token_text))

        with self.app.test_client() as c:
            ret = c.get("/v1/token-status", headers={"Authorization": f"bearer {token_text}"})
            self.assertEqual(ret.status_code, 200)
            self.assertEqual(g.authenticated_user, user)
            self.assertEqual(typing.cast(dict, ret.get_json()).get("status"), "welcome")
            json_user = _get_json_data(ret)
            self.assertEqual(json_user.get("username"), "test.hase")

        with self.app.test_client() as c:
            ret = c.get("/v1/token-status", headers={"Authorization": f"Bearer {token_text}"})
            self.assertEqual(ret.status_code, 200)

        with self.app.test_client() as c:
            ret = c.get("/v1/token-status", headers={"Authorization": f"BEARER {token_text}"})
        self.assertEqual(ret.status_code, 200)

    def test_search_no_token(self):
        ret = self.client.get("/v1/search?value=grunz")
        self.assertEqual(ret.status_code, 401)

    def test_search_token(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        user.tokens.append(Token(token=token_text))

        with self.app.test_client() as c:
            ret = c.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
            self.assertEqual(ret.status_code, 200)
            self.assertEqual(g.authenticated_user, user)

    def test_invalid_token(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        user.tokens.append(Token(token=token_text))

        with self.app.test_client() as c:
            ret = c.get("/v1/search?value=grunz", headers={"Authorization": f"bearer oink{token_text}"})
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.authenticated_user)

    def test_invalid_header(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        user.tokens.append(Token(token=token_text))

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer"})
        self.assertEqual(ret.status_code, 406)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"{token_text}"})
        self.assertEqual(ret.status_code, 406)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"oink {token_text}"})
        self.assertEqual(ret.status_code, 406)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text} oink"})
        self.assertEqual(ret.status_code, 406)

    def test_deactivated(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        user.tokens.append(Token(token=token_text))
        user.is_active = False

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
        self.assertEqual(ret.status_code, 401)

    def test_deleted(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        token = Token(token=token_text, user=user)
        token.deleted = True
        user.tokens.append(token)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
        self.assertEqual(ret.status_code, 401)

    def test_expired(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschwein"
        token = Token(token=token_text, user=user)
        token.expiresAt = datetime.datetime.now() - datetime.timedelta(weeks=1)
        user.tokens.append(token)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
        self.assertEqual(ret.status_code, 401)

    def test_update_expiration_auto(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschein"
        token = Token(
            token=token_text,
            user=user,
            source="auto",
            expiresAt=datetime.datetime.now() + datetime.timedelta(hours=1),
        )
        user.tokens.append(token)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
        self.assertEqual(ret.status_code, 200)

        db_token = Token.query.get(token.id)
        self.assertLess(
            abs(db_token.expiresAt - (datetime.datetime.now() + Token.defaultExpiration)),
            datetime.timedelta(minutes=1),
        )

    def test_update_expiration_manual(self):
        user = _create_user(name="test.hase")
        token_text = "geheimschein"
        expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
        token = Token(token=token_text, user=user, source="manual", expiresAt=expiration)
        user.tokens.append(token)

        ret = self.client.get("/v1/search?value=grunz", headers={"Authorization": f"bearer {token_text}"})
        self.assertEqual(ret.status_code, 200)

        db_token = Token.query.get(token.id)
        self.assertEqual(db_token.expiresAt, expiration)


class TestWebAuthn(RouteBase):
    def test_signin_request(self):
        with self.client:
            ret = self.client.post("/v1/webauthn/signin-request", json={"username": self.username})
            self.assertIsNotNone(session.get("expected_challenge"))
            self.assertEqual(session.get("username"), self.username)
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertFalse(data["passwordDisabled"])
        self.assertEqual(data["options"]["rpId"], "localhost")
        self.assertIsNotNone(data["options"]["challenge"])
        self.assertListEqual(data["options"]["allowCredentials"], [])

    def test_signin_request_password_disabled(self):
        self.user.password_disabled = True
        db.session.commit()

        with self.client:
            ret = self.client.post("/v1/webauthn/signin-request", json={"username": self.username})
            self.assertIsNotNone(session.get("expected_challenge"))
            self.assertEqual(session.get("username"), self.username)
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertTrue(data["passwordDisabled"])
        self.assertEqual(data["options"]["rpId"], "localhost")
        self.assertIsNotNone(data["options"]["challenge"])
        self.assertListEqual(data["options"]["allowCredentials"], [])

    def test_signin_request_with_keys(self):
        passkey_id = b"4711"
        self.user.passkeys = [PassKey(id=passkey_id, name="something")]
        db.session.commit()

        ret = self.client.post("/v1/webauthn/signin-request", json={"username": self.username})
        self.assertEqual(ret.status_code, 200)
        data = _get_json_data(ret)
        self.assertListEqual(
            data["options"]["allowCredentials"],
            [{"type": "public-key", "id": base64.urlsafe_b64encode(passkey_id).decode("utf-8").replace("=", "")}],
        )

    def test_signin_request_invalid_username(self):
        with self.client:
            ret = self.client.post("/v1/webauthn/signin-request", json={"username": "spektrophilious dackelschwanz"})
            self.assertEqual(ret.status_code, 200)
            self.assertIsNone(session.get("expected_challenge"))
            self.assertIsNone(session.get("username"))
        data = _get_json_data(ret)
        self.assertFalse(data["passwordDisabled"])
        self.assertEqual(data["options"]["rpId"], "localhost")
        self.assertListEqual(data["options"]["allowCredentials"], [])

    def test_signin_request_user_disabled(self):
        passkey_id = b"4711"
        self.user.passkeys = [PassKey(id=passkey_id, name="something")]
        self.user.is_active = False
        db.session.commit()

        with self.client:
            ret = self.client.post("/v1/webauthn/signin-request", json={"username": self.username})
            self.assertEqual(ret.status_code, 200)
            self.assertIsNone(session.get("expected_challenge"))
            self.assertIsNone(session.get("username"))

        data = _get_json_data(ret)

        self.assertFalse(data["passwordDisabled"])
        self.assertListEqual(data["options"]["allowCredentials"], [])

    def test_signin(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        self.app.config["BACKEND_URL"] = "http://localhost:7660"

        key_id = base64url_to_bytes(
            "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw"
        )
        self.user.passkeys = [
            PassKey(
                id=key_id,
                name="testhase",
                public_key=base64url_to_bytes(
                    "pQECAyYgASFYIC9xK9phz-T0Ls3r5coIy1wPk-TBFuPjKjTHD3ttKKU_Ilggp-l4S1SEgoUVQyyyxNc80iRnJ10YA3A50LoPsawEP18="
                ),
                current_sign_count=3,
            )
        ]

        test_credential = {
            "authenticatorAttachment": "cross-platform",
            "clientExtensionResults": {},
            "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "response": {
                "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAABg",
                "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiNWNCT2FMOHhQUllTSEU2a3cyVllhd2JXRG9tZ2oyeUxwcEJ2ekU3NndCQmNkOGZyeWY1bFF6aHhQaXYxcGJPWDB5QmxmX3VUbGRLLTNLOW11UHkwY0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                "signature": "MEYCIQDzOkUVKPYLkI1h-aCd9575HJ8t1PMfeWF_dm_cscU8zAIhAOV07U2yHfkB0oQvSXrpPLnynHn79GySRA5Sa350v6RW",
                "userHandle": "",
            },
            "type": "public-key",
        }
        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "5cBOaL8xPRYSHE6kw2VYawbWDomgj2yLppBvzE76wBBcd8fryf5lQzhxPiv1pbOX0yBlf_uTldK-3K9muPy0cA"
            )
            session["username"] = self.username

        with self.app.test_client() as c:
            ret = self.client.post("/v1/webauthn/signin", json=test_credential)
            self.assertEqual(ret.status_code, 200)
            self.assertIn("authenticated_user", g)
            self.assertEqual(g.authenticated_user, self.user)

        data = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertIn("id", data)
        self.assertIn("generatedToken", data)
        self.assertIn("expiresAt", data)

        self.assertEqual(len(self.user.tokens), 1)
        db_token = Token.query.filter(Token.id == data["id"]).first()
        self.assertIsNotNone(db_token)
        self.assertEqual(db_token.source, "auto")
        self.assertTrue(
            abs(db_token.expiresAt - (datetime.datetime.now() + Token.defaultExpiration))
            < datetime.timedelta(minutes=1)
        )

        db_key = PassKey.query.filter(PassKey.id == key_id).one()
        self.assertEqual(db_key.login_count, 1)
        self.assertTrue(db_key.last_used > (datetime.datetime.now() - datetime.timedelta(minutes=1)))

        self.app.config["BACKEND_URL"] = old_backend_url

    def test_signin_bad_challenge(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        self.app.config["BACKEND_URL"] = "http://localhost:7660"

        key_id = base64url_to_bytes(
            "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw"
        )
        self.user.passkeys = [
            PassKey(
                id=key_id,
                name="testhase",
                public_key=base64url_to_bytes(
                    "pQECAyYgASFYIC9xK9phz-T0Ls3r5coIy1wPk-TBFuPjKjTHD3ttKKU_Ilggp-l4S1SEgoUVQyyyxNc80iRnJ10YA3A50LoPsawEP18="
                ),
                current_sign_count=3,
            )
        ]

        test_credential = {
            "authenticatorAttachment": "cross-platform",
            "clientExtensionResults": {},
            "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "response": {
                "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAABg",
                "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiNWNCT2FMOHhQUllTSEU2a3cyVllhd2JXRG9tZ2oyeUxwcEJ2ekU3NndCQmNkOGZyeWY1bFF6aHhQaXYxcGJPWDB5QmxmX3VUbGRLLTNLOW11UHkwY0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                "signature": "MEYCIQDzOkUVKPYLkI1h-aCd9575HJ8t1PMfeWF_dm_cscU8zAIhAOV07U2yHfkB0oQvSXrpPLnynHn79GySRA5Sa350v6RW",
                "userHandle": "",
            },
            "type": "public-key",
        }
        with self.client.session_transaction() as session:
            session["expected_challenge"] = b"oink"
            session["username"] = self.username

        ret = self.client.post("/v1/webauthn/signin", json=test_credential)
        self.assertEqual(ret.status_code, 401)

        self.app.config["BACKEND_URL"] = old_backend_url

    def test_signin_normalize_url(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        old_frontend_url = self.app.config.get("FRONTEND_URL")

        key_id = base64url_to_bytes(
            "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw"
        )
        self.user.passkeys = [
            PassKey(
                id=key_id,
                name="testhase",
                public_key=base64url_to_bytes(
                    "pQECAyYgASFYIC9xK9phz-T0Ls3r5coIy1wPk-TBFuPjKjTHD3ttKKU_Ilggp-l4S1SEgoUVQyyyxNc80iRnJ10YA3A50LoPsawEP18="
                ),
                current_sign_count=3,
            )
        ]

        test_credential = {
            "authenticatorAttachment": "cross-platform",
            "clientExtensionResults": {},
            "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "response": {
                "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAABg",
                "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiNWNCT2FMOHhQUllTSEU2a3cyVllhd2JXRG9tZ2oyeUxwcEJ2ekU3NndCQmNkOGZyeWY1bFF6aHhQaXYxcGJPWDB5QmxmX3VUbGRLLTNLOW11UHkwY0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                "signature": "MEYCIQDzOkUVKPYLkI1h-aCd9575HJ8t1PMfeWF_dm_cscU8zAIhAOV07U2yHfkB0oQvSXrpPLnynHn79GySRA5Sa350v6RW",
                "userHandle": "",
            },
            "type": "public-key",
        }
        self.app.config["FRONTEND_URL"] = None
        self.app.config["BACKEND_URL"] = "http://localhost:7660/"
        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "5cBOaL8xPRYSHE6kw2VYawbWDomgj2yLppBvzE76wBBcd8fryf5lQzhxPiv1pbOX0yBlf_uTldK-3K9muPy0cA"
            )
            session["username"] = self.username

        with self.app.test_client() as c:
            ret = self.client.post("/v1/webauthn/signin", json=test_credential)
            self.assertEqual(ret.status_code, 200)
            self.assertIn("authenticated_user", g)
            self.assertEqual(g.authenticated_user, self.user)

        # justin case
        self.app.config["FRONTEND_URL"] = None
        self.app.config["BACKEND_URL"] = "http://localhost:7660/oink"
        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "5cBOaL8xPRYSHE6kw2VYawbWDomgj2yLppBvzE76wBBcd8fryf5lQzhxPiv1pbOX0yBlf_uTldK-3K9muPy0cA"
            )
            session["username"] = self.username

        with self.app.test_client() as c:
            ret = self.client.post("/v1/webauthn/signin", json=test_credential)
            self.assertEqual(ret.status_code, 200)
            self.assertIn("authenticated_user", g)
            self.assertEqual(g.authenticated_user, self.user)

        # frontend url should beat backend url for origin
        self.app.config["FRONTEND_URL"] = "http://localhost:7660/ui"
        self.app.config["BACKEND_URL"] = "http://some.where/else"
        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "5cBOaL8xPRYSHE6kw2VYawbWDomgj2yLppBvzE76wBBcd8fryf5lQzhxPiv1pbOX0yBlf_uTldK-3K9muPy0cA"
            )
            session["username"] = self.username

        with self.app.test_client() as c:
            ret = self.client.post("/v1/webauthn/signin", json=test_credential)
            self.assertEqual(ret.status_code, 200)
            self.assertIn("authenticated_user", g)
            self.assertEqual(g.authenticated_user, self.user)

        self.app.config["FRONTEND_URL"] = old_frontend_url
        self.app.config["BACKEND_URL"] = old_backend_url

    def test_signin_passkey_not_found(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        self.app.config["BACKEND_URL"] = "http://localhost:7660"

        other_user = _create_user(name="oink.hase")
        key_id = base64url_to_bytes(
            "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw"
        )
        other_user.passkeys = [
            PassKey(
                id=key_id,
                name="testhase",
                public_key=base64url_to_bytes(
                    "pQECAyYgASFYIC9xK9phz-T0Ls3r5coIy1wPk-TBFuPjKjTHD3ttKKU_Ilggp-l4S1SEgoUVQyyyxNc80iRnJ10YA3A50LoPsawEP18="
                ),
                current_sign_count=3,
            )
        ]
        db.session.commit()

        test_credential = {
            "authenticatorAttachment": "cross-platform",
            "clientExtensionResults": {},
            "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "response": {
                "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAABg",
                "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiNWNCT2FMOHhQUllTSEU2a3cyVllhd2JXRG9tZ2oyeUxwcEJ2ekU3NndCQmNkOGZyeWY1bFF6aHhQaXYxcGJPWDB5QmxmX3VUbGRLLTNLOW11UHkwY0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                "signature": "MEYCIQDzOkUVKPYLkI1h-aCd9575HJ8t1PMfeWF_dm_cscU8zAIhAOV07U2yHfkB0oQvSXrpPLnynHn79GySRA5Sa350v6RW",
                "userHandle": "",
            },
            "type": "public-key",
        }
        with self.client.session_transaction() as session:
            session["expected_challenge"] = b"oink"
            session["username"] = self.username

        ret = self.client.post("/v1/webauthn/signin", json=test_credential)
        self.assertEqual(ret.status_code, 401)

        self.app.config["BACKEND_URL"] = old_backend_url

    def test_signin_disabled(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        self.app.config["BACKEND_URL"] = "http://localhost:7660"

        key_id = base64url_to_bytes(
            "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw"
        )
        self.user.passkeys = [
            PassKey(
                id=key_id,
                name="testhase",
                public_key=base64url_to_bytes(
                    "pQECAyYgASFYIC9xK9phz-T0Ls3r5coIy1wPk-TBFuPjKjTHD3ttKKU_Ilggp-l4S1SEgoUVQyyyxNc80iRnJ10YA3A50LoPsawEP18="
                ),
                current_sign_count=3,
            )
        ]

        test_credential = {
            "authenticatorAttachment": "cross-platform",
            "clientExtensionResults": {},
            "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
            "response": {
                "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAABg",
                "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiNWNCT2FMOHhQUllTSEU2a3cyVllhd2JXRG9tZ2oyeUxwcEJ2ekU3NndCQmNkOGZyeWY1bFF6aHhQaXYxcGJPWDB5QmxmX3VUbGRLLTNLOW11UHkwY0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                "signature": "MEYCIQDzOkUVKPYLkI1h-aCd9575HJ8t1PMfeWF_dm_cscU8zAIhAOV07U2yHfkB0oQvSXrpPLnynHn79GySRA5Sa350v6RW",
                "userHandle": "",
            },
            "type": "public-key",
        }
        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "5cBOaL8xPRYSHE6kw2VYawbWDomgj2yLppBvzE76wBBcd8fryf5lQzhxPiv1pbOX0yBlf_uTldK-3K9muPy0cA"
            )
            session["username"] = self.username

        self.user.is_active = False
        db.session.commit()

        with self.app.test_client() as c:
            ret = self.client.post("/v1/webauthn/signin", json=test_credential)
            self.assertEqual(ret.status_code, 401)
            self.assertIsNone(g.get("authenticated_user"))

        self.app.config["BACKEND_URL"] = old_backend_url

    def test_create_options(self):
        with self.fake_auth(), self.client:
            ret = self.client.get("/v1/webauthn/create-options")
            self.assertIsNotNone(session.get("expected_challenge"))
        self.assertEqual(ret.status_code, 200)
        opts = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertEqual(opts["publicKey"]["user"]["name"], self.username)
        self.assertEqual(
            opts["publicKey"]["user"]["id"],
            base64.urlsafe_b64encode(self.user.passkey_id.encode("utf-8")).decode("utf-8"),
        )

        self.assertEqual(opts["publicKey"]["rp"]["id"], "localhost")

    def test_create_options_hostname(self):
        old_backend_url = self.app.config["BACKEND_URL"]
        self.app.config["BACKEND_URL"] = "https://oi.nk:1234/"

        with self.fake_auth():
            ret = self.client.get("/v1/webauthn/create-options")
        self.assertEqual(ret.status_code, 200)

        opts = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertEqual(opts["publicKey"]["rp"]["id"], "oi.nk")
        self.app.config["BACKEND_URL"] = old_backend_url

    def test_create_options_hostname_override(self):
        old_config = self.app.config["FRONTEND_URL"]
        self.app.config["FRONTEND_URL"] = "https://gru.nzoi.nk:1234/"

        with self.fake_auth():
            ret = self.client.get("/v1/webauthn/create-options")
        self.assertEqual(ret.status_code, 200)

        opts = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertEqual(opts["publicKey"]["rp"]["id"], "gru.nzoi.nk")
        self.app.config["FRONTEND_URL"] = old_config

    def test_create_options_exclude(self):
        with self.fake_auth():
            ret = self.client.get("/v1/webauthn/create-options")
        self.assertEqual(ret.status_code, 200)

        opts = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertListEqual(opts["publicKey"]["excludeCredentials"], [])

    def test_create_options_exclude_has_key(self):
        passkey_id = b"4711"
        self.user.passkeys = [PassKey(id=passkey_id, name="something")]
        db.session.commit()

        with self.fake_auth():
            ret = self.client.get("/v1/webauthn/create-options")
        self.assertEqual(ret.status_code, 200)
        opts = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertListEqual(
            opts["publicKey"]["excludeCredentials"],
            [{"type": "public-key", "id": base64.urlsafe_b64encode(passkey_id).decode("utf-8").replace("=", "")}],
        )

    def test_register_credential(self):
        old_backend_url = self.app.config.get("BACKEND_URL")
        self.app.config["BACKEND_URL"] = "http://localhost:7660"

        test_credential = {
            "name": "yubioink",
            "credential": {
                "id": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
                "rawId": "uD77zFgDembepzZtlffgWvHuJJPm_bCBDignwGhBY6vs42IupPXlGAKVyShfkdH-FAXcv8QDiZ_MW2Z5ma4HAw",
                "response": {
                    "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVjESZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAwAAAAAAAAAAAAAAAAAAAAAAQLg--8xYA3pm3qc2bZX34Frx7iST5v2wgQ4oJ8BoQWOr7ONiLqT15RgClckoX5HR_hQF3L_EA4mfzFtmeZmuBwOlAQIDJiABIVggL3Er2mHP5PQuzevlygjLXA-T5MEW4-MqNMcPe20opT8iWCCn6XhLVISChRVDLLLE1zzSJGcnXRgDcDnQug-xrAQ_Xw",
                    "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiLTM1MzRycWN0VVZ5SUpIUDlCMVZPQVBJY3JpVXFzUlRidjc0bTV5WHlTaFZwbWFQQzVjTURWT19KdDd1X3R5NXJPQ0tlRnZKT3pRMk9wSW85dHp4SkEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0Ojc2NjAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
                },
                "type": "public-key",
            },
            "public_key": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEL3Er2mHP5PQuzevlygjLXA-T5MEW4-MqNMcPe20opT-n6XhLVISChRVDLLLE1zzSJGcnXRgDcDnQug-xrAQ_Xw",
        }

        with self.client.session_transaction() as session:
            session["expected_challenge"] = base64url_to_bytes(
                "-3534rqctUVyIJHP9B1VOAPIcriUqsRTbv74m5yXyShVpmaPC5cMDVO_Jt7u_ty5rOCKeFvJOzQ2OpIo9tzxJA"
            )

        with self.fake_auth():
            ret = self.client.post("/v1/webauthn/register", json=test_credential)
        self.assertEqual(ret.status_code, 200)

        db_user = User.query.filter(User.username == self.username).first()
        self.assertEqual(len(db_user.passkeys), 1)
        self.assertIsNotNone(db_user.passkeys[0].public_key)
        self.assertEqual(db_user.passkeys[0].current_sign_count, 3)

        data = typing.cast(dict, ret.get_json()).get("data", {})
        self.assertEqual(data["name"], "yubioink")
        self.app.config["BACKEND_URL"] = old_backend_url
