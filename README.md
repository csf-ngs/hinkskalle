# Hinkskalle

[![Build Status](https://knecht.testha.se/api/badges/csf-ngs/hinkskalle/status.svg)](https://knecht.testha.se/csf-ngs/hinkskalle)

On-Premises Container Registry for OCI/[docker](https://www.docker.com/) and [singularity](https://github.com/sylabs/singularity)

<!--more-->

## What Am I

(buckethead) - I can store, retrieve and manage [OCI](https://opencontainers.org/) and [singularity](https://sylabs.io/singularity/) containers in a central library.

Compatible with/re-implementation of the [singularity library protocol](https://github.com/singularityhub/library-api) and the [OCI distribution spec](https://docs.docker.com/registry/introduction/).

## Documentation

Installation + Usage instructions can be found here:

[https://testha.se/projects/hinkskalle/](https://testha.se/projects/hinkskalle/)

# Development

## Clone Current HEAD

```bash
git clone https://github.com/csf-ngs/hinkskalle.git
```

## Docker development environment

Achieve the best development experience with continuous reloads and frontend
builds! No need to set up/mess up your computer!

Hinkskalle comes with a development environment based on [docker-compose](https://docs.docker.com/compose/). 

The [ghcr.io/csf-ngs/hinkskalle-dev](https://github.com/csf-ngs/hinkskalle-dev) image contains a complete development environment. 

### First Setup

Initial setup (or maybe you want to reset your dev environment):

```bash
# (of course you can use your own favorite dummy secrets)
cat <<_EOF > conf/db_secrets.env
POSTGRES_PASSWORD=supersecret
_EOF

cat <<_EOF > conf/secrets.env
HINKSKALLE_SECRET_KEY=superdupersecret
DB_PASSWORD=supersecret
HINKSKALLE_LDAP_BIND_PASSWORD=superldapsecret
_EOF

cat <<_EOF > conf/slapd_secrets.env
LDAP_ROOT_PASSWORD=superrootsecret
LDAP_LOGIN_PASSWORD=superldapsecret
_EOF

# start hinkdb first to set up base database
docker-compose up -d hinkdb
# give it a second
# install current database schema
docker-compose run --rm api flask db upgrade

# set up first admin user
docker-compose run --rm api flask localdb add-user \
    -u admin.hase \
    -p oink \
    -e 'admin.hase@testha.se' \
    -f Admin \
    -l Hase \
    --admin
# set up a normal user
docker-compose run --rm api flask localdb add-user \
    -u test.hase \
    -p oink \
    -e 'test.hase@testha.se' \
    -f Test \
    -l Hase 

# ONLY when you need to reset the dev env: clean everything
docker-compose down
docker-compose config --volumes | xargs docker volume rm 
```

### Running Development Instances

Dev server: [http://localhost:7660](http://localhost:7660)

```bash
# WARNING: On first startup we need to install node modules and build the frontend
# this might take a few minutes and the dev server will show
# The requested URL was not found on the server. until that's done.
#
# Whole stack (rarely needed)
docker-compose up -d
# bare minimum
docker-compose up -d api build_frontend
# log output
docker-compose logs -f
```

The current working directory (base) is mounted into the relevant containers.
You can edit the source files with your favorite editor/IDE directly. Services
will automatically rebuild and/or restart on changes.

This starts the following services:

#### `api`: Local Backend Instance at port 7660

Using [script/start-dev.sh](script/start-dev.sh). Restarts on changes in backend/

#### `build_frontend`: Continuous Frontend Build

Using [script/start-dev-frontend.sh](script/start-dev-frontend.sh), basically a `yarn build --watch`

#### `hinkdb`: Postgres database

#### `rq_scheduler`, `rq_worker`, `redis`: Backend async job queue (optional)

#### `ldap`: for testing LDAP authentication (optional)

#### `hockeypuck`, `hockeypuck_db`: PGP keyserver (optional)

### Side Notes

- uploaded images are stored in `./tmp`

## Development Install

Needs postgresql dev libraries! Install according to your OS instructions, e.g.:

```bash
# mac os x
brew install postgresql
# ubuntu/debian
apt install postgresql-dev
# etc.
```

```bash
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
```

This will also install nose2, Jinja2, fakeredis and psycopg2 for running tests
and generating typescript classes.

You also need to set up [Node](https://nodejs.org/en/),
[Vue](https://vuejs.org/) and [vue-cli](https://cli.vuejs.org/) for testing and
compiling the frontend:

```bash
# install node according to your OS
cd frontend/
yarn install
```

## Patch Singularity

***Not necessary for singularity v3.9.0 or newer***

Singularity absolutely required that the library server is reachable via https.
While you can set this up for your development server, it's much easier to
patch the source code and recompile your own.

The necessary patch is provided in
[share/singularity-plain-http.patch](share/singularity-plain-http.patch) and
should work an all versions.

ORAS requires a similar patch. If you want to play around with that, apply [share/oras-plain-http.patch](share/oras-plain-http.patch).

Follow the instructions on
[https://sylabs.io/guides/3.7/admin-guide/installation.html](https://sylabs.io/guides/3.7/admin-guide/installation.html)
(adjust for the version you would like) and apply the patch between the steps
"Checkout Code from Git" and "Compile Singularity":

```bash
cd ${GOPATH}/src/github.com/sylabs/singularity
patch -p1 < /path/to/singularity-plain-http.patch
patch -p1 < /path/to/oras-plain-http.patch
```

## Start Development Server

```bash
script/start-dev.sh
# continuous build of frontend
script/start-dev-frontend.sh
# (optional: start rq worker)
# script/start-dev-worker.sh
```

## Backend Tests

```bash
cd backend
nose2
```

## Frontend Tests

```bash
cd frontend
yarn test:unit
```

## OCI Conformance Tests

Requires a docker image built from
[https://github.com/opencontainers/distribution-spec/tree/main/conformance](https://github.com/opencontainers/distribution-spec/tree/main/conformance). 

```bash
cd share/oci
./conformance-test.sh
```

Your backend should be available at localhost:7660 

## Generate Typescript Classes for models

```bash
pip3 install git+https://github.com/csf-ngs/swagspotta
# make sure your local dev server is running at localhost:7660
share/generate-models.sh
```

# Built With

- [Python Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Vue.js](https://vuejs.org/)

# Contributing

Please do!

# Authors

- [Heinz Axelsson-Ekker](https://github.com/h3kker) - *initial work* - [VBCF Next Generation Sequencing](https://www.viennabiocenter.org/facilities/next-generation-sequencing/)

# License

This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details

