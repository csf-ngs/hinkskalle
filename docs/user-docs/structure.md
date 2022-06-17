---
Title: 'Library Structure'
weight: 10
---

## Library Structure

A Library path looks like this: `/entity/collection/container:tag`

### Entity

This is the basic (root) element. You are an entity called muh.kuh. You can do whatever you like underneath that!

We also have a special entity default with some general purpose containers and data.

### Collection

You can group/organize your containers and data into collections. It's up to you how that looks. As an inspiration: This might be by type (docker, singularity, ...) or by project or by purpose.

### Container

Now we're getting there, slowly. They contain images and tags pointing to images (and manifests, minor technical detail). Basically you push your data to a container and link it with a tag.

### Image

Some piece of data you push to us. Most likely, a singularity image. Can also be a docker container layer or some (any) data (if you use oras or the hinkskalle CLI).

This data is stored on the server and represented as an image linked to a container

You can address/retrieve an image by its sha256 hash

### Tag

Since hashes are a bit annoying to handle, you can give your image a name: the tag. This can be anything (within character limitation reasons), most commonly a version number (like when you type docker pull ubuntu:20.04).

### Examples

You're working on a project 'smurf-seq' where you need some tools:

- /muh.kuh/smurf-seq/samtools:v1.9
- /muh.kuh/smurf-seq/bedtools:v2.28.0
- /muh.kuh/smurf-seq/minimap2:v2.17

You decide to organize your genome references and indexes:

- /muh.kuh/genomes/hg19:bowtie2
- /muh.kuh/genomes/hg19:fasta
- /muh.kuh/genomes/hg19:kallisto
- /muh.kuh/genomes/tair10:bowtie2
- /muh.kuh/genomes/tair10:fasta
- /muh.kuh/genomes/tair10:kallisto

and so on.