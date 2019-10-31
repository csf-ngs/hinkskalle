# Hinkskalle

(buckethead)

Partial implementation of the Sylab's singularity library protocol [https://cloud.sylabs.io/library](https://cloud.sylabs.io/library)

### Should be able to do:

- `singularity pull library://entity/collection/container:tag`
- `singularity push -U image.sif library://entity/collection/container:tag`
- `singularity search resi # where is my cow?`

entities, collections and containers are created on push

### Auxiliary:

- `singularity remote add testhase https://singularity.ngs.vbcf.ac.at/`
- `singularity remote use testhase`
- `singularity remote login` 

### Login (token) is necessary for pushing images:

- use Forskalle API token
- require admin auth for push

### Bonus! Implement shub push:

- `singularity pull shub://singularity.ngs.vbcf.ac.at/collection/container:tag`

shub protocol does not have `entity`, create default entity (empty name)

can use `singularity push -U library:///collection/container:tag` to push there.

### Access Control

Pull is public for all!

Pushing is restricted to Forskalle users.

- all fsk users can create and push under their own entity (= username)
- all fsk users can create a collection under the default entity, which belongs to them then
- admins can push anywhere.

collections + containers have private flags. Entities have `defaultPrivate`
flag. But this is not implmented, since it cannot be changed with the
singularity cli.

### Tagging

automatically advance latest tag to last push. Could be handled differently (and now is under our control) (theoretically at least)

## Motivation

sregistry sucks! 

### Bloated

- postgres
- uwsgi container
- nginx
- redis
- celery worker

repo is 2 GB!

docker image + docker-compose config default awful:

- 5 GB docker image
- postgres + redis exposed on network

### Operating sucks

had to hack it to

- make ldap work (should be out of the box)
- some weird API change bugs

pushes just disappear, turns out to be permissions issue. Try to find logs!

### UI Sucks

- half of the things don't work
- confusing 
- no good structure (e.g. no view for all tags per image)

### Overengineered

see redis, celery, ip rate limiting, ...

mostly not needed

e.g. uploads handled by nginx; cannot properly check before upload + maybe cannot even signal failures? see above.

### Updating Bad

- have to make changes to the code (config)
- update is merge
- last time I tried requests just died and I didn't even find log messages

### sregistry client sucks

don't even begin to understand motivation behind the structure

- has local database (sqlite)
- some kind of internal storage/mirror
- does weird things (doubling of config keys WITH ALL CAPS)
- try to fish out pulled images!

-> want to have singularity push, but it speaks only library://

author currently implementing library://, but not convinced by the git commits


