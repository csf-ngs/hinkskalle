from setuptools import setup

test_deps = [
  'nose2',
  'fakeredis',
]
extras = [
  'test': test_deps,
]

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
        'ldap3',
        'Flask-RQ2',
    ],
    extra_requires={
      'dev': ['Jinja2'],
      'test': test_deps,
    },
)
