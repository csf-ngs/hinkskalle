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

## Installing

## Running Tests

# Deployment

# Built With

- [Python Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Vue.js](https://vuejs.org/)

# Contributing

# Authors

- [Heinz Axelsson-Ekker](https://github.com/h3kker) - *intiial work* - [VBCF Next Generation Sequencing](https://www.viennabiocenter.org/facilities/next-generation-sequencing/)

# License

This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details

