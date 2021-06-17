# Hinkskalle

[![Build Status](https://drone.ngs-cloud.vbcf.ac.at/api/badges/ngs-software/Hinkskalle/status.svg)](https://drone.ngs-cloud.vbcf.ac.at/ngs-software/Hinkskalle)

(buckethead) - store and retrieve [singularity](https://sylabs.io/singularity/) containers in a central library.

Compatible with/re-implementation of Sylab's singularity library protocol: [https://cloud.sylabs.io/library](https://cloud.sylabs.io/library)

## Features

Hinkskalle is supposed to be lightweight!

- full library:// protocol (should be compatible to sylabs cloud), including architecture specific tags and signed containers (with public pgp keyserver or additional software)
- shub:// *pull only* for legacy clients and pipelines
- oras:// protocol support for push and pull (not very well tested)
- [OCI distribution spec compliance](https://github.com/opencontainers/distribution-spec) for [docker](https://docs.docker.com/registry/introduction/) and [oras](https://oras.land/) (not very well tested)
- simple container storage on local or network filesystems
- LDAP authentication
- Minimal permission system

If you need more features, take a look at [https://github.com/singularityhub/sregistry](sregistry)!

# Getting Started

## Using a singularity library:

- `singularity remote add testhase https://singularity.testha.se/`
- `singularity remote use testhase`
- `singularity remote login` 
- `singularity pull library://entity/collection/container:tag`
- `singularity push -U image.sif library://entity/collection/container:tag`
- `singularity search resi # where is my cow?`

## Prerequisites

Hinkskalle requires Python3+. A SQL database server (PostgreSQL, MySQL, ...) is
recommended, but entirely optional (sqlite is fine).

# Container Deployment

Using docker-compose.

- Get a docker-compose file (e.g. [share/deploy/docker-compose.yml](share/deploy/docker-compose.yml))

- Set up conf/hinkskalle.env, conf/secrets.env, conf/db_secrets.env (see examples in [share/deploy](share/deploy/))

- docker-compose run api bash

```
cd backend
flask localdb init
flask localdb add-user # admin
```

- fire up whole stack

- if using ldap 

```
docker-compose exec api bash
cd backend
flask ldap sync
```

# Deployment

## Download the source to a location of your choice

- latest release from the [release page](./releases) and unpack

### Install Required Python Packages

```
cd backend/
# with sqlite only
pip install .
# or with postgres
pip install '.[postgres]'
```

### Install Singularity

Set up singularity according to the [instructions on sylabs.io](https://sylabs.io/docs/#singularity)

It is required only for checking image signatures and showing the singularity
definition file on the web.

The singularity binary should end up in `$PATH` so that Hinkskalle can find it.
`/usr/local/bin`, the default, is usually fine.

### Configure Hinkskalle

Hinkskalle reads its configuration from JSON files. By default it looks for

- `conf/config.json`
- `conf/secrets.json` (optional)

My recommendation is to put passwords etc. in an extra file (which is in
[.gitignore](.gitignore)) to make it harder to accidentally commit your
credentials.

See [share/doc/CONFIG.md](share/doc/CONFIG.md) for valid configuration options.

## GnuPG Keyserver

Signed and verified images require a central lookup of public keys. singularity
provides the keys subcommand to manage your keys, upload them and search for
public keys. 

Since singularity can talk to any (public or not) keyserver, Hinkskalle does
not come with keyserver functionality. Instead you can point it either to any
keyserver (see [https://sks-keyservers.net/](https://sks-keyservers.net/) for a
list) or run something like
[HockeyPuck](https://github.com/hockeypuck/hockeypuck) yourself.

The config variable `KEYSERVER_URL` should point to the webserver of the
keyserver you have chosen.

# Development

## Clone Current HEAD

```bash
git clone https://github.com/csf-ngs/hinkskalle.git
```

## Development Install

```bash
cd backend/
pip install '.[dev]'
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

Singularity absolutely requires that the library server is reachable via https.
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

Achieve the best development experience with continuous reloads and frontend builds!

```bash
script/start-dev.sh
# continuous build of frontend
script/start-dev-frontend.sh
# (optional: start rq worker)
# script/start-dev-worker.sh
```

## Backend Tests

```bash
nose2
```

## Frontend Tests

```bash
yarn test:unit
```

## OCI Conformance Tests

Requires a docker image built from [https://github.com/opencontainers/distribution-spec/tree/main/conformance](https://github.com/opencontainers/distribution-spec/tree/main/conformance). The current docker URL points to our internal registry, which you might not have access to.

```bash
cd share/oci
./conformance-test.sh
```

# Built With

- [Python Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Vue.js](https://vuejs.org/)

# Contributing

# Authors

- [Heinz Axelsson-Ekker](https://github.com/h3kker) - *initial work* - [VBCF Next Generation Sequencing](https://www.viennabiocenter.org/facilities/next-generation-sequencing/)

# License

This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details

