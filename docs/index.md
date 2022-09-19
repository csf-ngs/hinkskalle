---
Title: Hinkskalle
repo: 'https://github.com/csf-ngs/hinkskalle'
weight: 10
---

On-Premises Container Registry for OCI/[docker](https://www.docker.com/) and [singularity](https://github.com/sylabs/singularity)/[apptainer](https://apptainer.org/)

- [Admin Documentation](./index.md): [Setup](./deployment.md) / [Configuration](./configuration.md) / [Clients](./clients.md) / [Quotas](./quotas.md)
- [User Documentation](./user-docs/)

<!--more-->

## What Am I

(buckethead) - I can store, retrieve and manage [OCI](https://opencontainers.org/) and [singularity](https://sylabs.io/singularity/)/[apptainer](https://apptainer.org/) containers in a central library.

Compatible with/re-implementation of the [singularity library protocol](https://github.com/singularityhub/library-api) and the [OCI distribution spec](https://docs.docker.com/registry/introduction/). 

## Features

Hinkskalle is supposed to be lightweight! If you need more (and a more mature system), take a look at [https://github.com/singularityhub/sregistry](sregistry)!

- simple container storage on local or network filesystems
- local users + LDAP authentication
- minimal permission system

### Singularity+Apptainer

- full library:// protocol (should be compatible to sylabs cloud), including architecture specific tags and signed containers (with public pgp keyserver or additional software)
- shub:// *pull only* for legacy clients and pipelines
- oras:// protocol support for push and pull (not very well tested)

### OCI/docker/podman

- [OCI distribution spec compliance](https://github.com/opencontainers/distribution-spec) for [docker](https://docs.docker.com/registry/introduction/) and [oras](https://oras.land/) (not very well tested)

## Clients

We can talk to:

- [singularity](https://sylabs.io/singularity/)/[apptainer](https://apptainer.org/)
- [docker](https://docker.com/)
- [podman](https://podman.io/)
- [oras](https://oras.land/)

Also check out the Hinkskalle API + CLI:

- [hinkskalle-api](https://github.com/csf-ngs/hinkskalle-api)

## GnuPG Keyserver

Signed and verified images require a central lookup of public keys. singularity
provides the keys subcommand to manage your keys, upload them and search for
public keys.

Since singularity can talk to any (public or not) keyserver, Hinkskalle does
not come with keyserver functionality. Instead you can point it either to any
keyserver (see [https://sks-keyservers.net/](https://sks-keyservers.net/) for a
list) or run something like
[HockeyPuck](https://github.com/hockeypuck/hockeypuck) yourself.

## Prerequisites

Hinkskalle requires Python3+. A SQL database server (PostgreSQL, MySQL, ...) is
recommended, but entirely optional (sqlite is fine).
