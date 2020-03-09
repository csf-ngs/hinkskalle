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
        'flask-rebar',
        'requests',
        'passlib',
    ],
)
