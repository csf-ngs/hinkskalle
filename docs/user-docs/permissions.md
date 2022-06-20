---
title: 'Permissions'
weight: 30
---

## Singularity/Apptainer Library

### -> ***Pull is Public*** <-

It's important to understand: Default Permissions are *Public*. Anyone who knows the library URI to your image can pull it, even if they're not logged in. Call me naive, but it's in the open spirit of science: Share your stuff.

However they would have to know the library URI: Because browsing other entities than your own is not possible.

You can lock down your containers (maybe they contain your deepest, darkest secrets) by setting the *Private* flag on them.

You can also set a collection to *private*, then all (new) containers in that collection will be private as well.

Or, for complete lockdown, set your entity to *defaultPrivate*. This means that anything new(!) you push will be private.

### Push is Private

You and only you can push to your entity `muh.kuh`. That's it!

### The `private` Flag

The `private` (resp. `defaultPrivate` on the entity) *only* controls defaults for new collections and containers. Anything collection in a `defaultPrivate` entity will be created `private`, any container in a `private` container will be created `private`.

This is most interesting for auto-vivification of collections and containers by pushing (e.g. you push library://user.name/does-not-exist/me-neither:latest, this will create both does-not-exist and me-neither).

It does not affect principle visibility: because your entity cannot be browsed via the API (hence: the web UI) anyways.

If you want to make shared collections, use [Groups](#groups)

## All Other Container Types (OCI, ORAS)

### Pull is Authenticated Only

Docker, ORAS and stuff uploaded with the hinkskalle CLI can be pulled by anyone who is known to the registry (authenticated users).

You can set the container or collection to Private to allow pull only for yourself.

For complete lockdown set your entity to defaultPrivate. This means that anything new(!) you push will be private.

### Push is Private

You and only you can push to your entity muh.kuh. That's it!

## Special Case: Download Tokens

You can generate download URLs with the hinkskalle CLI and the web interface that allow downloading of exactly this image for everyone having this URL without further authentication or authorization, even for private images. It contains a special token that is valid for one day by default (can be configured on the server).

## Groups

Since [v4.3.0](../../CHANGELOG.md#v430-2022-05-02) Hinkskalle supports Groups.

You can access the groups interface in the Web UI (Menu Drawer, second option below your profile page) and create new groups and decide which users can join. There are three levels of membership:

- `admin`: can read/write and add/remove members and change their membership
- `contributor`: can create collections and push containers
- `readonly`: may browse and pull containers

Group/shared containers can be pushed to the group instead of your entity, e.g. your group Testhasenteam:

- singularity/apptainer:`library://testhasenteam/pipelines/samtools`
- OCI, ORAS: `kubel.testha.se/testhasenteam/pipelines/samtools`

You can't grant access to collections/containers stored in your personal entity. However it is easy to push containers to two places: It will be only uploaded once, the second time just creates an additional link to an existing image.

There is currently no way to do this in the web interface, though.