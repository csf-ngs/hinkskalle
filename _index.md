---
Title: Hinkskalle
date: '2022-04-11'
---

Container registry for OCI/[docker](https://www.docker.com/) and [singularity](https://github.com/sylabs/singularity)

<!--more-->

[Container Deployment](./deployment) - [Installation](./installation) - [Configuration](./configuration)

## What Am I

(buckethead) - I can store, retrieve and manage [OCI](https://opencontainers.org/) and [singularity](https://sylabs.io/singularity/) containers in a central library.

Compatible with/re-implementation of the [singularity library protocol](https://github.com/singularityhub/library-api) and the [OCI distribution spec](https://docs.docker.com/registry/introduction/). 

## Features

Hinkskalle is supposed to be lightweight!

- simple container storage on local or network filesystems
- local users + LDAP authentication
- minimal permission system

### Singularity

- full library:// protocol (should be compatible to sylabs cloud), including architecture specific tags and signed containers (with public pgp keyserver or additional software)
- shub:// *pull only* for legacy clients and pipelines
- oras:// protocol support for push and pull (not very well tested)

### OCI/docker/podman

- [OCI distribution spec compliance](https://github.com/opencontainers/distribution-spec) for [docker](https://docs.docker.com/registry/introduction/) and [oras](https://oras.land/) (not very well tested)