from datetime import datetime, timedelta

from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase
from Hinkskalle.models import Adm, AdmSchema, AdmKeys


class TestAdm(ModelBase):
    def test_base(self):
        key = Adm(key=AdmKeys.ldap_sync_results, val={"knofel": 100})
        db.session.add(key)
        db.session.commit()

        fromDb = Adm.query.get(AdmKeys.ldap_sync_results)
        self.assertDictEqual(fromDb.val, {"knofel": 100})
        self.assertTrue(abs(fromDb.createdAt - datetime.now()) < timedelta(seconds=2))

    def test_schema(self):
        schema = AdmSchema()
        key = Adm(key=AdmKeys.ldap_sync_results, val={"knofel": 100})

        serialized = schema.dump(key)
        self.assertDictEqual(serialized["val"], {"knofel": 100})

    def test_deserialize(self):
        schema = AdmSchema()
        toParse = {
            "val": {
                "knofel": 100,
                "tausend": [1, 2, 1000],
            }
        }
        deserialized = schema.load(toParse)
        deserialized["key"] = AdmKeys.ldap_sync_results.name

        key = Adm(**deserialized)
        db.session.add(key)
        db.session.commit()

        fromDb = Adm.query.get(AdmKeys.ldap_sync_results)
        self.assertDictEqual(fromDb.val, toParse["val"])
