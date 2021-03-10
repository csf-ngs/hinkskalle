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

#### Install Singularity (optional)

Singularity itself is optional on the server and only required for some
features, e.g.  displaying the Singularity definition file in the web
interface. The registry works perfectly fine.

Set up singularity according to the [instructions on sylabs.io](https://sylabs.io/docs/#singularity)

#### 

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

