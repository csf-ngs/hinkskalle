---
title: 'Container Types'
weight: 20
---

## Singularity

Singularity is a nice and light-weight container format/runtime for HPC that you should definitely use. There is a single binary to build (with root permissions) and run (no root needed) your containers. More information: [https://singularity.hpcng.org/](https://singularity.hpcng.org/) and [https://sylabs.io/singularity/](https://sylabs.io/singularity/)

Hinkskalle supports singularity with the library protocol as well as oras.

### Library

Configure Hinkskalle as a known remote with a access token:

```bash
singularity remote add hinkskalle http://localhost:7660/
# paste token
singularity remote use hinkskalle
```
                  

After that you can push/pull your images:

```bash
singularity push yourimage.sif library://muh.kuh/[collection]/[container]:[tag]
singularity pull library://muh.kuh/[collection]/[container]:[tag]
```

### ORAS

```bash
export SINGULARITY_DOCKER_PASSWORD=[password]
export SINGULARITY_DOCKER_USERNAME=muh.kuh
singularity push yourimage.sif oras://localhost:7660/muh.kuh/[collection]/[container]:[tag]
```
                
## docker/podman

Hinkskalle can handle your OCI containers as well. Just tag them to the server and push:

```bash
docker login -u muh.kuh localhost:7660
docker push localhost:7660/muh.kuh/[collection]/[container]:[tag]
docker pull localhost:7660/muh.kuh/[collection]/[container]:[tag]
```

## ORAS

ORAS stands for OCI Registry As Storage and allows you to push arbitrary files/directories to a OCI registry. You need a command line client, see [ORAS](https://oras.land/#cli-installation).

```bash
oras login --insecure -u muh.kuh localhost:7660
oras push --plain-http localhost:7660/muh.kuh/[collection]/[container]:[tag] \
  file1 file2 ...
oras pull --plain-http localhost:7660/muh.kuh/[collection]/[container]:[tag] 
```