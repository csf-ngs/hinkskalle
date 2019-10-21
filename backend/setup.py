from setuptools import setup

setup(
    name='Hinkskalle',
    version='0.0.1',
    packages=['Hinkskalle'],
    include_package_data=True,
    install_requires=[
        'flask',
        'SimpleJSON',
        'pymongo',
        'flask-mongoengine',
        'mongomock',
        'flask-rebar',
        'requests',
        'forskalle-api @ git+https://ngs.vbcf.ac.at/repo/software/forskalle-api.git',
        'fsk-authenticator @ git+https://ngs.vbcf.ac.at/repo/ngs-software/fsk-authenticator.git',
    ],
)
