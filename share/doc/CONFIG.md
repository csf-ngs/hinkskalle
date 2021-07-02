# Configuration Values

Refer to
[https://flask.palletsprojects.com/en/1.1.x/config/](https://flask.palletsprojects.com/en/1.1.x/config/)
for general Flask configuration values.

### Flask Config Values

You might want to set these:

- `APPLICATION_ROOT` - path that the library is mounted under. Note that, at the last time of checking, singularity did not deal so well with libraries not on the root (`/`) path!
- `PERMANENT_SESSION_LIFETIME` - session cookie expiration time
- `SESSION_COOKIE_NAME` - name for cookie. Note that Hinkskalle does not use cookie-based sessions, only Authorization: Bearer tokens.

### Hinskalle Config Values

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

### RQ Worker/Redis config

See [https://python-rq.org/docs/workers/](https://python-rq.org/docs/workers/) for general config settings.

- `REDIS_URL` - where can we find our redis server?

### Secrets

try to keep these out of `config.json`!

- `DB_PASSWORD`
- `REDIS_PASSWORD`

### Auth/LDAP config

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
      "HOST": "ldap.testha.se",
      "PORT": 389,
      "BIND_DN": "cn=login,ou=Adm,dc=testha,dc=se",
      "BASE_DN": "ou=Accounts,dc=testha,dc=se",
      "BIND_PASSWORD": "put me in secrets.json!"
    }
  }
}
```

# Environment Overrides

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

This is superuseful for injecting configs and secrets when running Hinkskalle
in a container (e.g. docker)
