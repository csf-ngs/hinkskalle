## Database Migrations

See [Issue #51](https://github.com/csf-ngs/hinkskalle/issues/51): make sure that the `size` column in the tables `image` and `image_upload_url` are type `bigint`. A fresh database install should have this, but if not:

```sql
alter table image_upload_url alter column size TYPE BIGINT;
alter table image alter column size TYPE BIGINT;
```

# v4.6.0 (2022-10-17)

- #46: passwordless login with webauthn/fido2 tokens

Users can configure passwordless login with hardware tokens (YubiKey),
TouchID etc.

# v4.5.0 (2022-10-14)

- #45: default quota for new users. 

This is actually a major change to the way quotas are handled.
Make sure you read the [documentation](https://csf-ngs.github.io/hinkskalle/quotas.html)!

### Updating

New config option `DEFAULT_GROUP_QUOTA`: if unset (or `0`) groups
have unlimited quota (but are still subject to individual user quotas)

`DEFAULT_USER_QUOTA` existed before and defaults to `0` = unlimited.

# v4.4.1 (2022-09-30)

- fix multiple/arch-specific tag handling:
- old (non-arch-specific) tags treated like `DEFAULT_ARCH`
- `imageTags` of container only returns tags from `DEFAULT_ARCH`

# v4.4.0 (2022-06-24)

**NOTE** if you're using ldap, you now have to either:

- set the `HINKSKALLE_LDAP_ENABLED` environment variable to a true value (e.g. `1`)
- put `"ENABLED": true` in the AUTH/LDAP section of your `config.json`

- more flexible LDAP configuration: attribute mapping, filters

# v4.3.3 (2022-06-21)

- toggle between apptainer and singularity environments (contributed by @grisuthedragon)
- fix #37: always show side navigation drawer, manual toggle with burger menu (thanks @jonas-schulze for reporting)

# v4.3.2 (2022-06-15)

- `script/start.sh` no longer expects to be started from a particular directory
- use abs path for start CMD in docker container

# v4.3.1 (2022-05-24)

- fix #27: serialize invalid (legacy) usernames
- dev: run oci conformance tests in ci pipeline (#18)
- fix #12: use jsonb fields for postgresql
- fix: sqlite migrations need `batch_alter_table`


# v4.3.0 (2022-05-02)

- feature: groups/teams
- fix #22: api keys are stored as salted hashes
- fix #3: replace uploaded flag with upload state; do not clear image location when file not found (could just be temporarily mislaid)
- fix: better handling of disabled ldap auth
- fix: complain when no secret key is configured
- dev: update flask and flask-rebar to latest
- dev: update vue + dependencies
- docs: example deployment fixed
- dev: build docker image from scratch without the vbcf.ngs base image
- dev: set up drone ci/cd

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
