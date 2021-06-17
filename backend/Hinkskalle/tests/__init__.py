from Hinkskalle import create_app
import os

os.environ['SQLALCHEMY_DATABASE_URI']='sqlite://'
os.environ['RQ_CONNECTION_CLASS']='fakeredis.FakeStrictRedis'
os.environ['HINKSKALLE_SECRET_KEY']='superdupersecret'

app = create_app()
app.config['TESTING']=True
app.testing=True