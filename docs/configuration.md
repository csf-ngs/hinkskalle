---
title: Configuration
weight: 3
---

Configuration Values

<!--more-->

Configuration is read from a file specified by the environment variable `HINKSKALLE_SETTINGS` or `conf/config.json` by default.

## Frontend Config

Make sure that these environment variables are to your taste:

- `HINKSKALLE_BACKEND_URL`: should point to the (public) URL that your backend API can be reached at. 
- `HINKSKALLE_ENABLE_REGISTER`: should the frontend allow "register new account" on the login page (default: off) (also switches off the signup routes in the backend)
- `HINKSKALLE_SINGULARITY_COMMAND`: command to show in help or copy for pull, defaults to `singularity`, could of course also be `apptainer` in your environment

## Flask

Refer to
[https://flask.palletsprojects.com/en/2.1.x/config/](https://flask.palletsprojects.com/en/2.1.x/config/)
for general Flask configuration values.

You might want to set these:

- `APPLICATION_ROOT` - path that the library is mounted under. Note that, at the last time of checking, singularity did not deal so well with libraries not on the root (`/`) path!
- `PERMANENT_SESSION_LIFETIME` - session cookie expiration time
- `SESSION_COOKIE_NAME` - name for cookie. Note that Hinkskalle does not use cookie-based sessions, only Authorization: Bearer tokens.

## Hinkskalle 

- `IMAGE_PATH` - where should we store the uploaded images?
- `IMAGE_PATH_HASH_LEVEL` - how many subdirectories should be created below IMAGE_PATH using the image has. Eg. the default: `2` would produce `IMAGE_PATH/a/b/sha256.abxxxxx`. Some file system types don't like directories with too many files in them. Applies only to new uploads.
- `FRONTEND_PATH` - where can we find `index.html` and the js bundles for the frontend, usually `../frontend/dist/`
- `PREFERRED_URL_SCHEME` - `(http|https)`: for generating URLs. If we run behind a reverse proxy we might think that we are on plain http. Use this to force https
- `UPLOAD_CHUNK_SIZE` - buffer this many bytes before dumping to disk during upload. Find a balance between upload speed and memory usage!
- `MULTIPART_UPLOAD_CHUNK` - for v2 multipart uploads. The singularity client splits images into chunks of this size.
- `DEFAULT_ARCH` - which archtitecture should we use for the default `latest` tag if no explicit tag is specified for a push (default `amd64`)
- `DEFAULT_USER_QUOTA` - in bytes, how much space to allow for images per user entity. 0 to disable (= default)
- `DOWNLOAD_TOKEN_EXPIRATION` - in seconds, how long should download links be valid. Each token grants access to images in specific manifests and should be handled with care.
- `SQLALCHEMY_DATABASE_URI` - database location. E.g. `sqlite:///data/db/hinkskalle.db`, or `postgresql+psycopg2://knihskalle:%PASSWORD%@hinkdb/hinkskalle"`. Any `%PASSWORD%` string will be replaced by the config value for `DB_PASSWORD`
- `KEYSERVER_URL` - public key storage/search. Hinkskalle does not come with its own keyserver. Point this to a compatible GnuPG keyserver (see [https://sks-keyservers.net/](https://sks-keyservers.net/) for a list). You can also run your own: [https://github.com/hockeypuck/hockeypuck](https://github.com/hockeypuck/hockeypuck)
- `SQLALCHEMY_TRACK_MODIFICATIONS` - leave this to false

## RQ Worker/Redis

See [https://python-rq.org/docs/workers/](https://python-rq.org/docs/workers/) for general config settings.

- `REDIS_URL` - where can we find our redis server?

## Maintenance Tasks

Configure a key `CRON` in `config.json` (times are in UTC!):

```json
{
  "CRON": {
    "expire_images": "46 21 * * *",
    "check_quotas": "48 21 * * *",
    "ldap_sync_results": "1,11,21,31,41,51 * * * *"
  }
}
```

Available tasks:

- `expire_images`: delete image files that have reached their `expiresAt` data (e.g. temporary uploads)
- `check_quotas`: recalculate space usage for all entities.
- `ldap_sync_results`: sync user database with LDAP server. You might not need this.

## Secrets

try to keep these out of `config.json`!

- `SECRET_KEY` for JWT token signing. *Important*: could be used to download any and all of your containers, do not leak!
- `DB_PASSWORD`  for postgresql db
- `REDIS_PASSWORD` for redis (job queue)

## Auth/LDAP 

- `AUTH.LDAP.ENABLED` - defaults to false, whether we should use LDAP or not
- `AUTH.LDAP.HOST` - where to find the ldap server
- `AUTH.LDAP.PORT` - which port (default: 389)
- `AUTH.LDAP.BIND_DN` - initial bind - this DN must be able to look up user accounts by username/email
- `AUTH.LDAP.BIND_PASSWORD` - should be in secrets.json
- `AUTH.LDAP.BASE_DN` - search base for user accounts

```json
{
  ...
  "AUTH": {
    "LDAP": {
      "ENABLED": true,
      "HOST": "ldap.testha.se",
      "PORT": 389,
      "BIND_DN": "cn=login,ou=Adm,dc=testha,dc=se",
      "BASE_DN": "ou=Accounts,dc=testha,dc=se",
      "BIND_PASSWORD": "put me in secrets.json!"
    }
  }
}
```

### Fine Tuning

You should be fine if you've got a fairly standard LDAP setup. But since everybody's mileage varies:

#### Custom Search Filters

- `AUTH.LDAP.FILTERS` 

How we look for users in your LDAP directory:

```json
          "FILTERS": {
              "user": "(&(uid={})(objectClass=person))",
              "all_users": "(objectClass=person)"
          },
```

The `user` filter is used during login: we replace the `{}` with whatever comes from the username field of the login form (properly escaped, duh) and we try to authenticate to the LDAP server using the entry we found + the provided password (rebind auth).

Be very careful what you put there, it determines who has access as who! You might want to have additional restrictions (e.g. memberOf=Somegroup) or different objectClass, ...

`all_users` tells us which users we synchronise with the Hinkskalle database. All entries returned are added during sync.

#### Attribute Mapping

- `AUTH.LDAP.ATTRIBUTES`

A map of hinkskalle user attributes to LDAP attributes, defaults to:

```json
          "ATTRIBUTES": {
              "username": "uid",
              "email": "mail",
              "firstname": "givenName",
              "lastname": "sn"
          }
```

Most interesting maybe: The `username` mapping - it must be unique in Hinkskalle and it is also used as the name of the entity (namespace) of the user.

## Environment Overrides

Certain variables from the config file(s) can be set via the environment. If
hinkskalle finds them there, it will overwrite the values:

- `DB_PASSWORD`
- `SQLALCHEMY_DATABASE_URI`
- `PREFERRED_URL_SCHEME`
- `HINKSKALLE_KEYSERVER_URL`
- `HINKSKALLE_REDIS_URL`
- `HINKSKALLE_LDAP_HOST`
- `HINKSKALLE_LDAP_PORT`
- `HINKSKALLE_LDAP_BIND_DN`
- `HINKSKALLE_LDAP_BIND_PASSWORD`
- `HINKSKALLE_LDAP_BASE_DN`
- `HINKSKALLE_SECRET_KEY`
- `HINKSKALLE_BACKEND_URL`
- `HINKSKALLE_ENABLE_REGISTER`
- `HINKSKALLE_SINGULARITY_COMMAND`

This is superuseful for injecting configs and secrets when running Hinkskalle
in a container (e.g. docker)

If using docker deployments you should also set the environment variables

- `POSTGRES_PASSWORD`

for the database initialization. It should match `DB_PASSWORD`. in addition make sure that

- `POSTGRES_DB`
- `POSTGRES_USER`

are set and match your sqlalchemy database uri.

Refer to the [official docker image docs](https://hub.docker.com/_/postgres)