import unittest
from Hinkskalle import db
import os
from . import app


class ModelBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        os.environ["RQ_CONNECTION_CLASS"] = "fakeredis.FakeStrictRedis"

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["DEFAULT_USER_QUOTA"] = 0
        self.app.config["DEFAULT_GROUP_QUOTA"] = 0
        self.app.config["SINGULARITY_FLAVOR"] = "singularity"
        self.app.config["ENABLE_REGISTER"] = False
        self.app.app_context().push()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        db.session.close()
        db.drop_all()
