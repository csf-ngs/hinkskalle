import typing
import unittest
import tempfile
import json

import os

from Hinkskalle import create_app
from Hinkskalle.util.auth.ldap import LDAPUsers
from Hinkskalle.util.auth.local import LocalUsers


def _test_conf():
    return {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "APPLICATION_ROOT": "/oink",
        "SECRET_KEY": "supergeheim",
    }


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.saved_environ = os.environ
        os.environ.clear()

    def tearDown(self):
        os.environ.update(self.saved_environ)

    def test_file(self):
        cf = tempfile.NamedTemporaryFile(mode="w")

        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        json.dump(_test_conf(), cf)
        cf.flush()
        test_app = create_app()

        self.assertEqual(test_app.config.get("APPLICATION_ROOT"), "/oink")
        self.assertEqual(test_app.config.get("SQLALCHEMY_DATABASE_URI"), "sqlite:///:memory:")

    def test_password_checkers_config(self):
        cf = tempfile.NamedTemporaryFile(mode="w")

        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        json.dump(_test_conf(), cf)
        cf.flush()

        from Hinkskalle import password_checkers

        self.assertEqual(len(password_checkers.checkers), 1)
        self.assertIsInstance(password_checkers.checkers[0], LocalUsers)

    def test_secrets(self):
        """an optional secrets config should override values from the main config"""
        cf = tempfile.NamedTemporaryFile(mode="w")
        secrets = tempfile.NamedTemporaryFile(mode="w")

        test_conf = _test_conf()
        test_conf["CANARY"] = "bird"
        json.dump(_test_conf(), cf)
        secrets_conf = {"CANARY": "yellow"}
        json.dump(secrets_conf, secrets)
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        os.environ["HINKSKALLE_SECRETS"] = secrets.name

        cf.flush()
        secrets.flush()

        test_app = create_app()
        self.assertEqual(test_app.config.get("CANARY"), "yellow")

    def test_secret_key_required(self):
        cf = tempfile.NamedTemporaryFile(mode="w")
        test_conf = _test_conf()
        test_conf.pop("SECRET_KEY")
        json.dump(test_conf, cf)
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        cf.flush()

        with self.assertRaisesRegex(Exception, r"SECRET_KEY"):
            test_app = create_app()
        os.environ["HINKSKALLE_SECRET_KEY"] = "saugeheim"
        test_app = create_app()
        self.assertEqual(test_app.config.get("SECRET_KEY"), "saugeheim")

    def test_db_config(self):
        cf = tempfile.NamedTemporaryFile(mode="w")
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        test_conf = _test_conf()
        test_conf["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://knihskalle:%PASSWORD%@hinkdb/hinkskalle"
        test_conf["DB_PASSWORD"] = "supersecret"

        json.dump(test_conf, cf)
        cf.flush()

        test_app = create_app()
        self.assertEqual(
            test_app.config.get("SQLALCHEMY_DATABASE_URI"),
            "postgresql+psycopg2://knihskalle:supersecret@hinkdb/hinkskalle",
        )

        os.environ["DB_PASSWORD"] = "anothersecret"
        test_app = create_app()
        self.assertEqual(
            test_app.config.get("SQLALCHEMY_DATABASE_URI"),
            "postgresql+psycopg2://knihskalle:anothersecret@hinkdb/hinkskalle",
        )

        os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://oink:%PASSWORD%@oink/oink"
        test_app = create_app()
        self.assertEqual(
            test_app.config.get("SQLALCHEMY_DATABASE_URI"), "postgresql+psycopg2://oink:anothersecret@oink/oink"
        )

    def test_url_scheme(self):
        cf = tempfile.NamedTemporaryFile(mode="w")
        test_conf = _test_conf()
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        json.dump(test_conf, cf)
        cf.flush()

        test_app = create_app()
        self.assertEqual(test_app.config.get("PREFERRED_URL_SCHEME"), "http")

        test_conf["PREFERRED_URL_SCHEME"] = "oink"
        cf.truncate()
        cf.seek(0)
        json.dump(test_conf, cf)
        cf.flush()
        test_app = create_app()
        self.assertEqual(test_app.config.get("PREFERRED_URL_SCHEME"), "oink")

        os.environ["PREFERRED_URL_SCHEME"] = "miau"
        test_app = create_app()
        self.assertEqual(test_app.config.get("PREFERRED_URL_SCHEME"), "miau")

    def test_keyserver(self):
        cf = tempfile.NamedTemporaryFile(mode="w")
        test_conf = _test_conf()
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        json.dump(test_conf, cf)
        cf.flush()

        test_app = create_app()
        self.assertEqual(test_app.config.get("KEYSERVER_URL"), "https://sks.hnet.se")

        test_conf["KEYSERVER_URL"] = "oink"
        cf.truncate()
        cf.seek(0)
        json.dump(test_conf, cf)
        cf.flush()
        test_app = create_app()
        self.assertEqual(test_app.config.get("KEYSERVER_URL"), "oink")

        os.environ["HINKSKALLE_KEYSERVER_URL"] = "miau"
        test_app = create_app()
        self.assertEqual(test_app.config.get("KEYSERVER_URL"), "miau")

    def test_ldap(self):
        cf = tempfile.NamedTemporaryFile(mode="w")
        test_conf: dict[str, typing.Any] = _test_conf()
        os.environ["HINKSKALLE_SETTINGS"] = cf.name
        json.dump(test_conf, cf)
        cf.flush()

        test_app = create_app()
        self.assertNotIn("LDAP", test_app.config["AUTH"])

        test_conf["AUTH"] = {
            "LDAP": {
                "HOST": "ell dapsi",
                "BASE_DN": "base dn",
            }
        }
        cf.truncate()
        cf.seek(0)
        json.dump(test_conf, cf)
        cf.flush()

        test_app = create_app()
        self.assertDictContainsSubset(
            test_app.config["AUTH"]["LDAP"],
            {
                "HOST": "ell dapsi",
                "BASE_DN": "base dn",
            },
        )

        os.environ["HINKSKALLE_LDAP_ENABLED"] = "1"
        os.environ["HINKSKALLE_LDAP_HOST"] = "eins"
        os.environ["HINKSKALLE_LDAP_PORT"] = "2"
        os.environ["HINKSKALLE_LDAP_BIND_DN"] = "drei"

        test_app = create_app()
        self.assertDictContainsSubset(
            test_app.config["AUTH"]["LDAP"],
            {
                "ENABLED": True,
                "HOST": "eins",
                "PORT": "2",
                "BIND_DN": "drei",
                "BASE_DN": "base dn",
            },
        )

        from Hinkskalle import password_checkers

        self.assertEqual(len(password_checkers.checkers), 2)
        self.assertCountEqual([type(c) for c in password_checkers.checkers], [LocalUsers, LDAPUsers])
