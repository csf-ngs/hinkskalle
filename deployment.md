---
Title: 'Deployment with docker-compose'
date: '2022-04-11'
---

How to run hinkskalle as a container without local installation (recommende)

<!--more-->

- Get a docker-compose file. Why not this one: [docker-compose.yml](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/docker-compose.yml)?
- run `mkdir conf/`
- Set up 
  - [conf/config.json](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/config.json)
  - [conf/hinkskalle.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/hinkskalle.env)
  - [conf/secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/secrets.env)
  - [conf/db_secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/db_secrets.env)
  - see [configuration](../configuration) for details
- Initialize Database

```bash
docker-compose run api bash
cd backend
# installs database schema
flask localdb init
# create admin user
flask localdb add-user
```

- fire up whole stack with: `docker-compose up -d`
- if using ldap:

```bash
docker-compose exec api bash
cd backend
flask ldap sync
```

The example docker-compose starts a backend server on port 7600. You will want
to run it behind a reverse proxy serving via HTTPS (e.g. nginx, caddy, Apache,
...).

It also starts:

- PostgreSQL Server for metadata (only available within the docker-compose network)
- Redis Server for background/periodic job execution
- an [rq](https://python-rq.org/) worker to execute jobs
- an [rq-scheduler](https://github.com/rq/rq-scheduler) to manage periodic maintenance jobs

## Keyserver

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