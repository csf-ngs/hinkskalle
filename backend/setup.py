from setuptools import setup

setup(
    name='Hinkskalle',
    version='4.4.0',
    packages=['Hinkskalle'],
    include_package_data=True,
    install_requires=[
        'werkzeug>=2.0.0',
        'flask>=2.0.0',
        'Flask-SQLAlchemy',
        'Flask-Migrate',
        'Flask-Session',
        'flask-rebar>=2.2.1',
        'flask_wtf>=1.0.0',
        'SimpleJSON',
        'python-dotenv',
        'requests',
        'passlib',
        'Flask-RQ2',
        'ldap3',
        'pyjwt',
        'humanize',
        'python-slugify',
        'cryptography',
    ],
    extras_require={
      'dev': ['nose2','fakeredis','psycopg2', 'nose2-html-report', 'nose2[coverage_plugin]'],
      'test': ['nose2', 'fakeredis'],
      'postgres': ['psycopg2'],
    },
)
