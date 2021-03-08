from setuptools import setup

setup(
    name='Hinkskalle',
    version='2.0.3',
    packages=['Hinkskalle'],
    include_package_data=True,
    install_requires=[
        'flask',
        'SimpleJSON',
        'Flask-SQLAlchemy',
        'Flask-Migrate',
        'flask-rebar',
        'requests',
        'passlib',
        'Flask-RQ2',
        'ldap3',
    ],
    extras_require={
      'dev': ['Jinja2','nose2','fakeredis','psycopg2'],
      'test': ['nose2', 'fakeredis'],
      'postgres': ['psycopg2'],
    },
)
