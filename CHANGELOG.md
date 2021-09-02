# v4.2.9 (2021-09-02)

- fix entity/collection/container schemas
- OCI: fix x-docker-digest header, fetch manifest per container
- docs: fix model
- docs: update example docker-compose deployment
- dev: fix oci conformance test script
- dev: deployment starts redis server

# v4.2.8 (2021-07-31)

- view/run tasks in frontend
- cron scheduler for tasks

# v4.2.7 (2021-07-23)

- expiration date for images
- admin tokens of other users
- download timestamps for image, container, manifest
- about/help
- inline fonts, don't want external loading
- can set expiresAt + private flags on blob push (used by cli)

# v4.2.6 (2021-07-01)

- hopefully fixed env override for backend url

# v4.2.5 (2021-06-29)

- better handling of unauthenticated access
- oras/cli/docker usage info

# v4.2.4 (2021-06-27)

- description field not required (containers, collections)
- take hash from image if not specified in v2 upload init
- catch exceptions during rq job execution, log in job result
- more download options (cmd lines, ...)
- config for download token expiration 
- blob pulls get docker-content-digest headers to better check HEAD success
- allow caps in distribution names, convert to lower case

# v4.2.2 (2021-06-24)

- api error parsing, better token fail signaling
- return absolute location URLs for download tokens

# v4.2.1 (2021-06-23)

- cannot use : in staging filenames (CIFS don't like)

# v4.2.0 (2021-06-22)

- staged uploads if hinkskalle api and server have shared access to filesystem (config)
- sort by size

# v4.1.0 (2021-06-21)

- used size of entities, collections, containers
- can enforce quotas now
- latest uploads with container/tag types
- admin entity creates chowns to username corresponding to entity name; collection and container ownership sticky to entity
- token-status route returns user info

### Bugfixes

- default arch for tags with null arch
- respect entity defaultPrivate and collection private setting when creating containers by oci push
- deny entity/collection/container create by oci push for users where they should not be able to
- oci pulls increment download counters


# v4.0.1 (2021-06-17)

- close (all) temporary upload filehandles
- container/image type symbols in search results
- direct downloads for singularity + oras manifests

# v4.0.0 (2021-06-17)

- first release with full OCI/ORAS support (OCI conformance tests passing)

## Smaller Changes

- frontend uses current URL as window title
- cascading delete for containers

# v3.1.0 (2021-06-01)

- support for ORAS pull

# v3.0.2 (2021-05-26)

### Bugfixes

- case insensitive queries for entities, colllections, containers

# v3.0.1 (2021-05-10)

### Bugfixes

- size column needs to hold large values :-O
- fix ldap sync job retrieval
- create user entity on login
- fix docker build + tagging

# v3.0.0 (2021-05-07)

Release for general usage with local users, LDAP auth and web interface.

Also implements arch tags and multipart uploads

# v2.0.2 (2020-03-11)

initial public release, no changelog maintained before.
