from setuptools import setup

setup(
    name='Hinkskalle',
    version='4.2.7',
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
        'pyjwt',
        'humanize',
    ],
    extras_require={
      'dev': ['Jinja2','nose2','fakeredis','psycopg2'],
      'test': ['nose2', 'fakeredis'],
      'postgres': ['psycopg2'],
    },
)
