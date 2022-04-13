---
Title: 'Deployment with docker/docker-compose'
date: '2022-04-11'
---

## 

- Get a docker-compose file. Why not this one: [docker-compose.yml](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/docker-compose.yml)?
- run `mkdir conf/`
- Set up 
  - [conf/config.json](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/config.json)
  - [conf/hinkskalle.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/hinkskalle.env)
  - [conf/secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/secrets.env)
  - [conf/db_secrets.env](https://github.com/csf-ngs/hinkskalle/blob/master/share/deploy/conf/db_secrets.env)
  - see [configuration](../configuration) for details
- `docker-compose run api bash`

```bash
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


