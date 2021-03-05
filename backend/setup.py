from setuptools import setup

setup(
    name='Hinkskalle',
    version='2.0.1',
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
      'dev': ['Jinja2'],
      'test': ['nose2', 'fakeredis'],
      'postgres': ['psycopg2'],
    },
)
