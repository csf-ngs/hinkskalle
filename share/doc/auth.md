# Authentication, Authorization

## Local User Tables

user table with `m:n` to groups

### Access Control 

currently:

- can create entity with own username
- full control underneath own entity (search/push)
- can pull from `default` entity

- pull is public

`private` flag not implemented

#### Private Flag

First step: implement private flag:

- no pull/search except for self

#### Group Entities

- create and allow push+search for all members

#### ACLs

is that really necessary? would be nice to have

- "invite" other users to collection/container
- groups too?
- read-only and read-write
- read-write can then also create new containers inside collection etc

without ACLs maybe we don't need a complete user list (see below)

## Tokens

n tokens per user. Fine-grained authorization?

- rw tokens
- ro tokens for pulling only?

Create tokens in web interface (`/auth/tokens` is where the cli directs you to)

additionally upstream token verification:

- forward token to another backend
- backend returns user data if token valid

would be convenient for Forskalle, but any other backend would have to return a
defined JSON structure OR would need to implement configurable mapping (ugh)


## LDAP authentication

provide LDAP password check backend for login to web

almost have to synchronize LDAP user+group list with local tables, otherwise it
will be hard to define access (only users that have logged in available for searching??)

## Oauth

would be nice, too

but how to provide user list?
