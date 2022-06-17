---
Title: 'Clients'
weight: 4
---

How to use Hinkskalle in your pipelines/deployments

<!--more-->

## singularity

```bash
singularity remote add testhase https://kuebel.testha.se/
singularity remote use testhase
singularity remote login
singularity pull library://entity/collection/container:tag
singularity push -U image.sif library://entity/collection/container:tag
singularity search resi # where is my cow?
```

## apptainer

```bash
apptainer remote add testhase https://kuebel.testha.se/
apptainer remote use testhase
apptainer remote login
apptainer pull library://entity/collection/container:tag
apptainer push -U image.sif library://entity/collection/container:tag
apptainer search resi # where is my cow?
```

## docker

```bash
docker login -u user.name kuebel.testha.se 
docker tag my-container kuebel.testha.se/user.name/collection/my-container:latest
docker push kuebel.testha.se/user.name/collection/my-container:latest
docker pull kuebel.testha.se/user.name/collection/my-other-container:v0.0.7
```

## oras

```bash
oras login -u user.name kuebel.testha.se
oras push kuebel.testha.se/user.name/collection/my-container:latest [file1] [file2] ...
oras pull kuebel.testha.se/user.name/collection/my-other-container:latest
```
