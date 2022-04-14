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

Your backend should be available at localhost:7660 (default dev docker compose).

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

