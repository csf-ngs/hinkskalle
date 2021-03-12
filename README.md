# Hinkskalle

[![Build Status](https://drone.ngs-cloud.vbcf.ac.at/api/badges/ngs-software/Hinkskalle/status.svg)](https://drone.ngs-cloud.vbcf.ac.at/ngs-software/Hinkskalle)

(buckethead) - store and retrieve [singularity](https://sylabs.io/singularity/) containers in a central library.

Compatible with/re-implementation of Sylab's singularity library protocol: [https://cloud.sylabs.io/library](https://cloud.sylabs.io/library)

# Getting Started

### Using a singularity library:

- `singularity remote add testhase https://singularity.testha.se/`
- `singularity remote use testhase`
- `singularity remote login` 
- `singularity pull library://entity/collection/container:tag`
- `singularity push -U image.sif library://entity/collection/container:tag`
- `singularity search resi # where is my cow?`

## Prerequisites

Hinkskalle requires Python3+. A SQL database server (PostgreSQL, MySQL, ...) is
recommended, but entirely optional (sqlite is fine).

## Installing

#### Download the source to a location of your choice

- latest release from the [release page](./releases) and unpack
- or use `git clone https://github.com/h3kker/hinkskalle.git` for the latest development version

#### Install Required Python Packages

```
cd backend/
# with sqlite only
pip install .
# or with postgres
pip install '.[postgres]'
```

#### Install Singularity

Set up singularity according to the [instructions on sylabs.io](https://sylabs.io/docs/#singularity)

It is required only for checking image signatures and showing the singularity
definition file on the web.

The singularity binary should end up in `$PATH` so that Hinkskalle can find it.
`/usr/local/bin`, the default, is usually fine.

#### Configuration

Hinkskalle reads its configuration from JSON files. By default it looks for

- `conf/config.json`
- `conf/secrets.json` (optional)

My recommendation is to put passwords etc. in an extra file (which is in
[.gitignore](.gitignore)), which makes it harder to accidentally commit your
credentials.

See [share/doc/CONFIG.md](share/doc/CONFIG.md) for valid configuration options.

### Development Install

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

#### Start Development Server

Achieve the best development experience with continuous reloads and frontend builds!

```bash
script/start-dev.sh
# continuous build of frontend
script/start-dev-frontend.sh
# (optional: start rq worker)
# script/start-dev-worker.sh
```

#### Patch Singularity

Singularity absolutely requires that the library server is reachable via https.
While you can set this up for your development server, it's much easier to
patch the source code and recompile your own.

The necessary patch is provided in
[share/singularity-plain-http.patch](share/singularity-plain-http.patch) and
should work an all versions.

Follow the instructions on
[https://sylabs.io/guides/3.7/admin-guide/installation.html](https://sylabs.io/guides/3.7/admin-guide/installation.html)
(adjust for the version you would like) and apply the patch between the steps
"Checkout Code from Git" and "Compile Singularity":

```bash
cd ${GOPATH}/src/github.com/sylabs/singularity
patch -p1 < /path/to/singularity-plain-http.patch
```

#### Backend Tests

```bash
nose2
```

#### Frontend Tests

```bash
yarn test:unit
```

# Deployment

# Built With

- [Python Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Vue.js](https://vuejs.org/)

# Contributing

# Authors

- [Heinz Axelsson-Ekker](https://github.com/h3kker) - *initial work* - [VBCF Next Generation Sequencing](https://www.viennabiocenter.org/facilities/next-generation-sequencing/)

# License

This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details

