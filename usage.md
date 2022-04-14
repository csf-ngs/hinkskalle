---
Title: 'Usage'
---

How to use Hinkskalle in your pipelines/deployments

<!--more-->

## Using a singularity library:

```bash
singularity remote add testhase https://kuebel.testha.se/
singularity remote use testhase
singularity remote login
singularity pull library://entity/collection/container:tag
singularity push -U image.sif library://entity/collection/container:tag
singularity search resi # where is my cow?
```
