---
title: 'Permissions'
weight: 30
---

## Singularity Library

-> ***Pull is Public*** <-

It's important to understand: Default Permissions are *Public*. Anyone who knows the library URI to your image can pull it, even if they're not logged in. Call me naive, but it's in the open spirit of science: Share your stuff.

You can lock down your containers (maybe they contain your deepest, darkest secrets) by setting the *Private* flag on them.

You can also set a collection to *private*, then all (new) containers in that collection will be private as well.

Or, for complete lockdown, set your entity to *defaultPrivate*. This means that anything new(!) you push will be private.

### Push is Private

You and only you can push to your entity `muh.kuh`. That's it!

## All Other Containers

### Pull is Authenticated Only

Docker, ORAS and stuff uploaded with the hinkskalle CLI can be pulled by anyone who is known to the registry (authenticated users).

You can set the container or collection to Private to allow pull only for yourself.

For complete lockdown set your entity to defaultPrivate. This means that anything new(!) you push will be private.

### Push is Private

You and only you can push to your entity muh.kuh. That's it!

## Special Case: Download Tokens

You can generate download URLs with the hinkskalle CLI and the web interface that allow downloading of exactly this image for everyone having this URL without further authentication or authorization, even for private images. It contains a special token that is valid for one day by default (can be configured on the server).

## Groups/Teams

Sorry, not yet.