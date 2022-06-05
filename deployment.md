---
Title: 'Setup'
weight: 1
---

How to run hinkskalle as a container (recommended) or local installation

<!--more-->

## Deployment with docker-compose

Get a docker-compose file. Why not this one: [docker-compose.yml](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/docker-compose.yml)?

Apart from the application server listening on port 7660 this also starts:

- PostgreSQL Server for metadata (only available within the docker-compose network)
- Redis Server for background/periodic job execution
- an [rq](https://python-rq.org/) worker to execute jobs
- an [rq-scheduler](https://github.com/rq/rq-scheduler) to manage periodic maintenance jobs


### Configuration

See [configuration](../configuration) for details

- run `mkdir conf/`
- Set up 
  - [conf/config.json](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/config.json)
  - [conf/hinkskalle.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/hinkskalle.env)
  - [conf/secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/secrets.env)
  - [conf/db_secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/db_secrets.env)

### Database Setup

With the default docker-compose file:

```bash
# start db server first to trigger database initialization
docker-compose up -d hinkdb
docker-compose run api bash
# installs database schema
docker-compose run --rm api flask db upgrade
# create admin user
docker-compose run --rm api flask localdb add-user \
  -u admin.hase \
  -p somethingonlyyouknow \
  -e admin@testha.se \
  -f Admin -l Hase \
  --admin
# create regular user (or use web interface)
docker-compose run --rm api flask localdb add-user \
  -u user.hase \
  -p alsosomethingfairlysecret \
  -e user@testha.se \
  -f User -l Hase
```

### LDAP Setup (optional)

Initial sync all LDAP users:

```bash
docker-compose run --rm api flask ldap sync
```

### Startup

- fire up whole stack with: `docker-compose up -d`

### Reverse Proxy

The example docker-compose starts a backend server on port 7600. You will want
to run it behind a reverse proxy serving via HTTPS (e.g. nginx, caddy, Apache,
...).

### Keyserver

If you would like to run your own keyserver put something like this in your `docker-compose.yaml`:

```yaml
volumes:
  # ...
  hockeypuck_db:
  hockeypuck_data:
# ...
services:
  # ...
  hockeypuck:
    image: "ghcr.io/csf-ngs/hockeypuck"
    ports:
      - "11371:11371"
    depends_on:
      - hockeypuck_db
    volumes:
      - hockeypuck_data:/hockeypuck/data
  hockeypuck_db:
    image: postgres:12
    environment:
      - POSTGRES_USER=hkp
      - POSTGRES_DB=hkp
      - POSTGRES_PASSWORD=hkp ! <---  danger mouse
    volumes:
      - hockeypuck_db:/var/lib/postgresql/data
```

This will start an instance of [Hockeypuck](https://hockeypuck.io/). The config variable `KEYSERVER_URL` should point to `http://localhost:11371/`.

## Install from Source Code

- latest release from the [release page](https://github.com/csf-ngs/hinkskalle/tags) and unpack

### Required Python Packages

```
cd backend/
# with sqlite only
pip install .
# or with postgres
pip install '.[postgres]'
```

### Singularity Binaries

Set up singularity according to the [instructions on sylabs.io](https://sylabs.io/docs/#singularity)

It is required only for checking image signatures and showing the singularity
definition file on the web.

The singularity binary should end up in `$PATH` so that Hinkskalle can find it.
`/usr/local/bin`, the default, is usually fine.

### Configuration

Hinkskalle reads its configuration from JSON files. By default it looks for

- `conf/config.json`
- `conf/secrets.json` (optional)

My recommendation is to put passwords etc. in an extra file (which is in
[.gitignore](.gitignore)) to make it harder to accidentally commit your
credentials.

See [configuration](../configuration) for valid configuration options.