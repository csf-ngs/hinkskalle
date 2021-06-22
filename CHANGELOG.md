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
