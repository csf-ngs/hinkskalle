# Hinkskalle for File Exchange

## Intro

just a bunch of ideas:

can we use Hinkskalle as a File Exchange server to replace `filemanager/byurl`, also provide upload capabilities?

can not replace seqmate for sequencing data download + qc, would be additional: analysis data, long read data, pr0n; can handle uploads by user (which is a problem currently)

## Pro/Con

### Pro

- better access control (put it under user entity)
- organization in collection/container (don't call it container)
- web ui (listing, searching)
- easy to make download web interface
- cleanup/expiration 
- user quotas (not implemented yet)
- checksumming built in
- easy file sharing (just link image to container)

### Con

- upload overhead (could make custom API to move/link directly to image folder)
- 2 file platforms (seqmate unbeatable for sequencing data + qc)
- there must be more

### Remarks

- upload can be chunked and (with limits) resumable
- download monolithic though, no advantage over seqmate filemanager

# Usage 

oras install is simple binary dl

## Facility Upload

- oras push (can push files, but also directories: takes care of creating archive bundle + checksumming)
- custom cli for stuff like direct linking

## User Download

- web interface (files, archives)
- curl/wget et al (files, archives) 
- oras (transparent for archives)

## User Upload

- web interface (single files)
- curl/wget et al (single files)
- oras

# Needed

## Server

- "image" dl from web interface (easy)
- "image" upload via web interface (np)
- quotas (need anyways)
- differentiate containers to hold singularity/docker/general data
- views for different container types

## Client

- nothing!



